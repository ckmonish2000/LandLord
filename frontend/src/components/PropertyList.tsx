import type { Account, Property } from "../types";
import Avatar from "./Avatar";
import { BuildingIcon, PlusIcon, WarningIcon, WhatsappIcon } from "./Icons";
import { SkeletonList } from "./Skeleton";

interface Props {
  account: Account | null;
  properties: Property[] | null;
  loading: boolean;
  error: string | null;
  selectedId: string | null;
  onSelect: (p: Property) => void;
  onAdd: () => void;
  onRetry: () => void;
  onLink: () => void;
}

/** Middle column: the landlord's properties (one per WhatsApp group). */
export default function PropertyList({
  account,
  properties,
  loading,
  error,
  selectedId,
  onSelect,
  onAdd,
  onRetry,
  onLink,
}: Props) {
  const connected = account?.status === "connected";

  return (
    <section className="list-panel">
      <header className="list-header">
        <div className="list-title">
          <h2>Properties</h2>
          {properties && properties.length > 0 && (
            <span className="muted small">{properties.length} {properties.length === 1 ? "property" : "properties"}</span>
          )}
        </div>
        {connected && (
          <button className="btn btn-secondary btn-sm" onClick={onAdd}>
            <PlusIcon size={16} />
            Add property
          </button>
        )}
      </header>

      <div className="list-body">
        {!account && !loading && (
          <div className="empty">
            <WhatsappIcon size={32} className="empty-icon" />
            <h3>Link your WhatsApp</h3>
            <p className="muted">Your WhatsApp groups become the properties you manage here.</p>
            <button className="btn btn-primary" onClick={onLink}>Link WhatsApp</button>
          </div>
        )}

        {account && !connected && (
          <div className="empty">
            <WarningIcon size={32} className="empty-icon danger" />
            <h3>WhatsApp was logged out</h3>
            <p className="muted">This device was removed from your phone. Link it again to continue.</p>
            <button className="btn btn-primary" onClick={onLink}>Link again</button>
          </div>
        )}

        {loading && <SkeletonList rows={5} />}

        {!loading && error && (
          <div className="empty">
            <WarningIcon size={32} className="empty-icon danger" />
            <p className="form-error">{error}</p>
            <button className="btn btn-secondary" onClick={onRetry}>Try again</button>
          </div>
        )}

        {connected && !loading && !error && properties?.length === 0 && (
          <div className="empty">
            <BuildingIcon size={32} className="empty-icon" />
            <h3>No properties yet</h3>
            <p className="muted">Pick the WhatsApp group of a building to start recording its houses.</p>
            <button className="btn btn-primary" onClick={onAdd}>Add property</button>
          </div>
        )}

        {account &&
          !loading &&
          properties?.map((p) => (
            <button
              key={p.id}
              className={`list-item ${p.id === selectedId ? "selected" : ""}`}
              onClick={() => onSelect(p)}
            >
              <Avatar name={p.name} kind="group" size={44} />
              <div className="item-text">
                <div className="item-row">
                  <span className="item-title">{p.name || "Unnamed group"}</span>
                </div>
                <div className="item-row">
                  <span className="item-sub muted">Added {new Date(p.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </button>
          ))}
      </div>
    </section>
  );
}
