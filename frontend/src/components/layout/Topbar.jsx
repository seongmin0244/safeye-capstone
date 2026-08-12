import { useLocation } from "react-router-dom";
import { Menu } from "lucide-react";
import { getPageMeta } from "../../constants/menu";

function Topbar({ onToggleSidebar }) {
  const location = useLocation();
  const { title, desc } = getPageMeta(location.pathname);

  return (
    <header className="topbar">
      <button
        type="button"
        onClick={onToggleSidebar}
        aria-label="사이드바 열기/닫기"
        className="topbar-toggle"
      >
        <Menu size={20} />
      </button>
      <div className="topbar-text">
        <h1 className="topbar-title">{title}</h1>
        {desc && <p className="topbar-description">{desc}</p>}
      </div>
    </header>
  );
}

export default Topbar;
