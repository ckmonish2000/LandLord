import { formatPhone } from "../format";
import type { House, Property, PropertyMember } from "../types";
import Avatar from "./Avatar";
import { BuildingIcon, InfoIcon, MemberCardIcon } from "./Icons";
import { memberTitle } from "./MemberPanel";
import Modal from "./Modal";

/** Placeholder field: shows what will be collected later. Not editable or saved yet. */
interface PreviewField {
  label: string;
  example: string;
  hint?: string;
}

const HOUSE_FIELDS: PreviewField[] = [
  { label: "RR number", example: "e.g. 1234567890", hint: "From the electricity bill" },
  { label: "Water connection no.", example: "e.g. WC 20417" },
  { label: "Monthly rent", example: "e.g. ₹18,500" },
  { label: "Maintenance", example: "e.g. ₹2,250 per month" },
  { label: "Carpet area", example: "e.g. 1,140 sq ft" },
  { label: "Parking slot", example: "e.g. B2 14" },
];

const MEMBER_FIELDS: PreviewField[] = [
  { label: "Move in date", example: "e.g. 3 Mar 2025" },
  { label: "Lease ends", example: "e.g. 2 Mar 2026" },
  { label: "Security deposit", example: "e.g. ₹55,000" },
  { label: "Emergency contact", example: "e.g. +91 98450 31277" },
  { label: "ID proof", example: "e.g. Aadhaar ending 4821" },
  { label: "Vehicle number", example: "e.g. KA 03 MP 7719" },
];

function PreviewFields({ fields }: { fields: PreviewField[] }) {
  return (
    <>
      <div className="preview-note">
        <InfoIcon size={18} />
        <span>Preview. These fields are not saved yet; they show what this page will collect.</span>
      </div>
      <div className="form-grid">
        {fields.map((f) => (
          <label key={f.label} className="field">
            <span>{f.label}</span>
            <input placeholder={f.example} disabled />
            {f.hint && <small className="muted">{f.hint}</small>}
          </label>
        ))}
      </div>
    </>
  );
}

function roleLabel(m: PropertyMember): string {
  if (m.is_owner && m.lives_here) return "Owner, lives here";
  if (m.is_owner) return "Owner, lives elsewhere";
  return "Lives here";
}

const ComingSoonFooter = ({ onClose }: { onClose: () => void }) => (
  <>
    <button className="btn btn-ghost" onClick={onClose}>Close</button>
    <button className="btn btn-primary" disabled title="Coming soon">Save details</button>
  </>
);

export function HouseDetailsModal({
  house,
  property,
  people,
  onClose,
}: {
  house: House;
  property: Property;
  people: PropertyMember[];
  onClose: () => void;
}) {
  return (
    <Modal
      title={`House ${house.number}`}
      subtitle={`Floor ${house.floor} · ${property.name}`}
      icon={<BuildingIcon size={22} />}
      onClose={onClose}
      footer={<ComingSoonFooter onClose={onClose} />}
    >
      <section className="modal-section">
        <h3>People</h3>
        {people.length === 0 ? (
          <p className="muted small">Nobody is linked to this house.</p>
        ) : (
          <ul className="people-list">
            {people.map((m) => (
              <li key={m.jid}>
                <Avatar name={m.saved_name || m.push_name || m.phone || "?"} src={m.picture_url} size={32} />
                <span className="item-title">{memberTitle(m)}</span>
                <span className={`tag ${m.is_owner ? "accent" : ""}`}>{roleLabel(m)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="modal-section">
        <h3>House details</h3>
        <PreviewFields fields={HOUSE_FIELDS} />
      </section>
    </Modal>
  );
}

export function MemberDetailsModal({
  member,
  property,
  onClose,
}: {
  member: PropertyMember;
  property: Property;
  onClose: () => void;
}) {
  const phone = formatPhone(member.phone);
  return (
    <Modal
      title={memberTitle(member)}
      subtitle={[phone !== memberTitle(member) ? phone : null, member.push_name && `~ ${member.push_name}`]
        .filter(Boolean)
        .join(" · ") || property.name}
      icon={<MemberCardIcon size={22} />}
      onClose={onClose}
      footer={<ComingSoonFooter onClose={onClose} />}
    >
      <section className="modal-section">
        <h3>House</h3>
        {member.house ? (
          <div className="summary-card">
            <span className="summary-main mono">
              {member.house.number}
              <span className="muted"> · Floor {member.house.floor}</span>
            </span>
            <span className={`tag ${member.is_owner ? "accent" : ""}`}>{roleLabel(member)}</span>
          </div>
        ) : (
          <div className="summary-card">
            <span className="muted">
              {member.is_owner
                ? "Lives elsewhere. Tick Lives here in the table to add their house."
                : "Not linked yet. Tick Owner or Lives here in the table."}
            </span>
            {member.is_owner && <span className="tag accent">Owner</span>}
          </div>
        )}
      </section>
      <section className="modal-section">
        <h3>Member details</h3>
        <PreviewFields fields={MEMBER_FIELDS} />
      </section>
    </Modal>
  );
}
