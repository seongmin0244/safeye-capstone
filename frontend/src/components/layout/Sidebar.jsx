import { NavLink } from "react-router-dom";
import { MENU_GROUPS } from "../../constants/menu";

function Sidebar({ isOpen }) {
  return (
    <div
      className={`flex flex-col bg-sidebar h-screen p-4 transition-[width] duration-200 overflow-hidden ${
        isOpen ? "w-[260px]" : "w-16"
      }`}
    >
      <div className="flex items-center gap-2.5 px-3 pt-2 pb-7">
        <div className="w-8 h-8 rounded-lg bg-accent shrink-0" />
        {isOpen && (
          <div className="text-white font-bold text-[17px] tracking-tight">
            SAFEye
          </div>
        )}
      </div>

      {MENU_GROUPS.map((group) => (
        <div key={group.label} className="mb-5">
          {isOpen && (
            <p className="text-[11px] text-sidebar-muted mb-2 tracking-[0.05em] px-3">
              {group.label}
            </p>
          )}

          {group.items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-3 mb-1 rounded-[10px] no-underline ${
                    isActive
                      ? "bg-sidebar-active text-white"
                      : "bg-transparent text-sidebar-text"
                  }`
                }
              >
                <Icon size={20} />
                {isOpen && (
                  <>
                    <span className="flex-1 text-[14.5px] font-semibold">
                      {item.label}
                    </span>
                    {item.badge && (
                      <span className="bg-danger text-white text-[11px] font-bold rounded-full px-[7px] py-[1px]">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>
      ))}

      <div className="flex-1" />

      {isOpen && (
        <div className="p-3 text-[11.5px] text-sidebar-muted leading-relaxed">
          © 2026 SAFEye
          <br />
          안전관리 지원 시스템
        </div>
      )}
    </div>
  );
}

export default Sidebar;
