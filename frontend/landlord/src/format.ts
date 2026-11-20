/** 919876543210 -> "+91 98765 43210"; other numbers just get a "+". */
export function formatPhone(phone: string | null | undefined): string | null {
  if (!phone) return null;
  if (phone.length === 12 && phone.startsWith("91")) {
    return `+91 ${phone.slice(2, 7)} ${phone.slice(7)}`;
  }
  return `+${phone}`;
}

/** "Ravi Tenant" -> "RT". Letters only, so phone numbers give "" (caller shows an icon). */
export function initials(name: string): string {
  const parts = name.replace(/[^\p{L} ]/gu, "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "";
  return (parts[0][0] + (parts[1]?.[0] ?? "")).toUpperCase();
}
