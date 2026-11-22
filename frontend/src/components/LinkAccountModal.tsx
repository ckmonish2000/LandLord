import { useEffect, useState } from "react";
import { ApiError, api } from "../api";
import { QrIcon } from "./Icons";
import Modal from "./Modal";

const QR_REFRESH_MS = 15_000; // WhatsApp rotates the QR about every 20s
const POLL_MS = 3_000;

interface Props {
  onClose: () => void;
  onLinked: () => void;
}

/** Shows the QR from /whatsapp/qr and closes once the account appears as connected. */
export default function LinkAccountModal({ onClose, onLinked }: Props) {
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load the QR now and refresh it while the modal is open.
  useEffect(() => {
    let cancelled = false;
    let current: string | null = null;

    async function load() {
      try {
        const blob = await api.qr();
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        if (current) URL.revokeObjectURL(current);
        current = url;
        setQrUrl(url);
        setError(null);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 409) onLinked(); // already linked
        else setError(e instanceof Error ? e.message : "Could not load the QR code");
      }
    }

    load();
    const id = setInterval(load, QR_REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
      if (current) URL.revokeObjectURL(current);
    };
  }, [onLinked]);

  // Watch for the account to become connected after scanning.
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const accounts = await api.accounts();
        if (accounts.some((a) => a.status === "connected")) onLinked();
      } catch {
        /* keep polling */
      }
    }, POLL_MS);
    return () => clearInterval(id);
  }, [onLinked]);

  return (
    <Modal
      title="Link your WhatsApp"
      subtitle="Your groups become the properties you manage here."
      icon={<QrIcon />}
      onClose={onClose}
      width="sm"
    >
      <ol className="steps">
        <li>Open WhatsApp on your phone</li>
        <li>Go to Settings, then Linked devices, then Link a device</li>
        <li>Point your phone at this code</li>
      </ol>
      <div className="qr-box">
        {qrUrl ? (
          <img src={qrUrl} alt="WhatsApp link QR code" />
        ) : error ? (
          <p className="form-error">{error}</p>
        ) : (
          <span className="skeleton qr-skeleton" aria-label="Generating QR code" />
        )}
      </div>
      <p className="muted small center">The code refreshes on its own. This window closes once you are connected.</p>
    </Modal>
  );
}
