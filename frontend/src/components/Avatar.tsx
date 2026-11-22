import { useEffect, useState } from "react";
import { initials } from "../format";
import { GroupIcon, UserIcon } from "./Icons";

const PALETTE = ["#6b5b95", "#2a7f62", "#b5651d", "#3b6ea5", "#a23e48", "#6d8b3a", "#8a5a83", "#2f7a8c"];

function colorFor(seed: string): string {
  let h = 0;
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

interface Props {
  name: string;
  src?: string | null;
  size?: number;
  kind?: "person" | "group";
}

/** Photo if it loads, otherwise initials (people) or a group icon on a colored circle. */
export default function Avatar({ name, src, size = 48, kind = "person" }: Props) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);

  const style = { width: size, height: size, fontSize: size * 0.38 };
  if (src && !failed) {
    return (
      <img
        className="avatar"
        style={style}
        src={src}
        alt=""
        referrerPolicy="no-referrer"
        loading="lazy"
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <div className="avatar avatar-fallback" style={{ ...style, background: colorFor(name) }} aria-hidden>
      {kind === "group" ? <GroupIcon size={size * 0.5} /> : initials(name) || <UserIcon size={size * 0.5} />}
    </div>
  );
}
