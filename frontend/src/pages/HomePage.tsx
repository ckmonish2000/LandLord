import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import AccountRail from "../components/AccountRail";
import GroupList from "../components/GroupList";
import HouseFields from "../components/HouseFields";
import LinkAccountModal from "../components/LinkAccountModal";
import MemberPanel from "../components/MemberPanel";
import PropertyList from "../components/PropertyList";
import type { Account, Group, Member, Property, PropertyMember } from "../types";

const message = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

/** Runs `load` whenever `key` changes (null = nothing to load). Returns data / loading / error / reload. */
function useLoad<T>(key: string | null, load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setData(null);
    setError(null);
    if (key === null) return;

    let cancelled = false;
    setLoading(true);
    load()
      .then((d) => !cancelled && setData(d))
      .catch((e) => !cancelled && setError(message(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
      setLoading(false);
    };
    // `load` is recreated each render; `key` says when to refetch.
  }, [key, tick]);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data, setData, loading, error, reload };
}

export default function HomePage() {
  const { user, logout } = useAuth();

  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  const [linking, setLinking] = useState(false);

  // "properties": list of properties + selected property's members.
  // "add": pick a WhatsApp group, preview its members, add it as a property.
  const [view, setView] = useState<"properties" | "add">("properties");
  const [property, setProperty] = useState<Property | null>(null);
  const [group, setGroup] = useState<Group | null>(null);
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const account = accounts?.find((a) => a.id === accountId) ?? null;
  const connected = account?.status === "connected";

  const loadAccounts = useCallback(async () => {
    try {
      const list = await api.accounts();
      setAccounts(list);
      setAccountId((current) => (list.some((a) => a.id === current) ? current : list[0]?.id ?? null));
    } catch {
      setAccounts([]);
    }
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  const properties = useLoad(account ? `props:${account.id}` : null, api.properties);
  const groups = useLoad(connected && view === "add" ? `groups:${account!.id}` : null, api.groups);
  const groupMembers = useLoad<Member[]>(group ? `gm:${group.jid}` : null, () => api.members(group!.jid));
  const propertyMembers = useLoad<PropertyMember[]>(property ? `pm:${property.id}` : null, () =>
    api.propertyMembers(property!.id),
  );

  const addedJids = useMemo(() => new Set(properties.data?.map((p) => p.group_jid)), [properties.data]);
  const existing = group ? properties.data?.find((p) => p.group_jid === group.jid) ?? null : null;

  function openProperty(p: Property) {
    setView("properties");
    setGroup(null);
    setProperty(p);
  }

  function startAdding() {
    setView("add");
    setProperty(null);
    setGroup(null);
    setAddError(null);
  }

  function pickGroup(g: Group) {
    setGroup(g);
    setAddError(null);
  }

  async function addProperty() {
    if (!group) return;
    setAdding(true);
    setAddError(null);
    try {
      const created = await api.createProperty(group.jid);
      properties.setData((list) => [...(list ?? []), created]);
      openProperty(created);
    } catch (e) {
      setAddError(message(e));
    } finally {
      setAdding(false);
    }
  }

  const onLinked = useCallback(() => {
    setLinking(false);
    loadAccounts();
  }, [loadAccounts]);

  if (!user) return null;

  return (
    <div className="app-shell">
      <AccountRail
        user={user}
        accounts={accounts}
        selectedId={accountId}
        onSelect={(id) => {
          setAccountId(id);
          setView("properties");
          setProperty(null);
          setGroup(null);
        }}
        onLink={() => setLinking(true)}
        onLogout={logout}
      />

      {view === "add" ? (
        <GroupList
          account={account}
          groups={groups.data}
          loading={groups.loading}
          error={groups.error}
          selectedJid={group?.jid ?? null}
          onSelect={pickGroup}
          onRefresh={groups.reload}
          onLink={() => setLinking(true)}
          addedJids={addedJids}
          onBack={() => {
            setView("properties");
            setGroup(null);
          }}
        />
      ) : (
        <PropertyList
          account={account}
          properties={properties.data}
          loading={accounts === null || properties.loading}
          error={properties.error}
          selectedId={property?.id ?? null}
          onSelect={openProperty}
          onAdd={startAdding}
          onRetry={properties.reload}
          onLink={() => setLinking(true)}
        />
      )}

      {view === "add" ? (
        <MemberPanel
          subject={
            group && {
              name: group.name,
              pictureUrl: group.picture_url,
              subtitle: `${group.participant_count} members${group.topic ? ` · ${group.topic}` : ""}`,
            }
          }
          members={groupMembers.data}
          loading={groupMembers.loading}
          error={groupMembers.error}
          onRetry={groupMembers.reload}
          emptyTitle="Choose a group"
          emptyText="Pick the WhatsApp group of the property you want to add."
          headerAction={
            group && (
              <>
                {addError && <span className="form-error small">{addError}</span>}
                {existing ? (
                  <button className="btn-secondary" onClick={() => openProperty(existing)}>Open property</button>
                ) : (
                  <button className="btn-primary" onClick={addProperty} disabled={adding}>
                    {adding ? "Adding…" : "Add as property"}
                  </button>
                )}
              </>
            )
          }
        />
      ) : (
        <MemberPanel<PropertyMember>
          subject={
            property && {
              name: property.name,
              subtitle: "Enter each member's floor and house number",
            }
          }
          members={propertyMembers.data}
          loading={propertyMembers.loading}
          error={propertyMembers.error}
          onRetry={propertyMembers.reload}
          emptyTitle={properties.data?.length ? "Select a property" : "Add your first property"}
          emptyText={
            properties.data?.length
              ? "Pick a property on the left to see its members and houses."
              : "Each property is a WhatsApp group. Add one to record who lives where."
          }
          renderMemberExtra={(m) => (
            <HouseFields
              assignment={m}
              onSave={(value) => api.setMemberHouse(property!.id, m.jid, value)}
            />
          )}
        />
      )}

      {linking && <LinkAccountModal onClose={() => setLinking(false)} onLinked={onLinked} />}
    </div>
  );
}
