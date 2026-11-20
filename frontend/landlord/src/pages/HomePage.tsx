import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import AccountRail from "../components/AccountRail";
import GroupList from "../components/GroupList";
import LinkAccountModal from "../components/LinkAccountModal";
import MemberPanel from "../components/MemberPanel";
import type { Account, Group, Member } from "../types";

const message = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong");

export default function HomePage() {
  const { user, logout } = useAuth();

  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  const [linking, setLinking] = useState(false);

  const [groups, setGroups] = useState<Group[] | null>(null);
  const [groupsLoading, setGroupsLoading] = useState(false);
  const [groupsError, setGroupsError] = useState<string | null>(null);
  const [groupsReload, setGroupsReload] = useState(0);

  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<Member[] | null>(null);
  const [membersLoading, setMembersLoading] = useState(false);
  const [membersError, setMembersError] = useState<string | null>(null);
  const [membersReload, setMembersReload] = useState(0);

  const account = accounts?.find((a) => a.id === accountId) ?? null;

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

  // Groups of the selected (connected) account.
  useEffect(() => {
    setGroup(null);
    setGroups(null);
    setGroupsError(null);
    if (!account || account.status !== "connected") return;

    let cancelled = false;
    setGroupsLoading(true);
    api
      .groups()
      .then((g) => !cancelled && setGroups(g))
      .catch((e) => !cancelled && setGroupsError(message(e)))
      .finally(() => !cancelled && setGroupsLoading(false));
    return () => {
      cancelled = true;
    };
  }, [account?.id, account?.status, groupsReload]);

  // Members of the selected group.
  useEffect(() => {
    setMembers(null);
    setMembersError(null);
    if (!group) return;

    let cancelled = false;
    setMembersLoading(true);
    api
      .members(group.jid)
      .then((m) => !cancelled && setMembers(m))
      .catch((e) => !cancelled && setMembersError(message(e)))
      .finally(() => !cancelled && setMembersLoading(false));
    return () => {
      cancelled = true;
    };
  }, [group, membersReload]);

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
        onSelect={setAccountId}
        onLink={() => setLinking(true)}
        onLogout={logout}
      />
      <GroupList
        account={account}
        groups={groups}
        loading={accounts === null || groupsLoading}
        error={groupsError}
        selectedJid={group?.jid ?? null}
        onSelect={setGroup}
        onRefresh={() => setGroupsReload((n) => n + 1)}
        onLink={() => setLinking(true)}
      />
      <MemberPanel
        group={group}
        members={members}
        loading={membersLoading}
        error={membersError}
        onRetry={() => setMembersReload((n) => n + 1)}
      />
      {linking && <LinkAccountModal onClose={() => setLinking(false)} onLinked={onLinked} />}
    </div>
  );
}
