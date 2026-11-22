import { useEffect, useId, type ReactNode } from "react";
import { CloseIcon } from "./Icons";

interface Props {
  title: string;
  subtitle?: ReactNode;
  icon?: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
  width?: "sm" | "md";
  children: ReactNode;
}

/** Centered dialog. Closes on Escape, on the backdrop, and on the close button. */
export default function Modal({ title, subtitle, icon, onClose, footer, width = "md", children }: Props) {
  const titleId = useId();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div
        className={`modal modal-${width}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="modal-header">
          {icon && <span className="modal-icon">{icon}</span>}
          <div className="modal-titles">
            <h2 id={titleId}>{title}</h2>
            {subtitle && <p className="muted">{subtitle}</p>}
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close" autoFocus>
            <CloseIcon />
          </button>
        </header>
        <div className="modal-body">{children}</div>
        {footer && <footer className="modal-footer">{footer}</footer>}
      </div>
    </div>
  );
}
