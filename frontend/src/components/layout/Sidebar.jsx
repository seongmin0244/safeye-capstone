import { NavLink } from "react-router-dom";
import { MENU_GROUPS } from "../../constants/menu";

function Sidebar({ isOpen }) {
  return (
    <div
      style={{
        width: isOpen ? "200px" : "64px",
        borderRight: "1px solid #eee",
        padding: "16px",
        minHeight: "100vh",
        transition: "width 0.2s ease",
        overflow: "hidden",
      }}
    >
      <h3 style={{ marginBottom: "20px" }}>{isOpen ? "Safeye" : "SE"}</h3>

      {MENU_GROUPS.map((group) => (
        <div key={group.label} style={{ marginBottom: "20px" }}>
          {isOpen && (
            <p
              style={{
                fontSize: "11px",
                color: "#999",
                marginBottom: "8px",
                letterSpacing: "0.05em",
              }}
            >
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
                style={({ isActive }) => ({
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 10px",
                  marginBottom: "4px",
                  borderRadius: "6px",
                  textDecoration: "none",
                  backgroundColor: isActive ? "#333" : "transparent",
                  color: isActive ? "#fff" : "#333",
                })}
              >
                <Icon size={16} />
                {isOpen && (
                  <>
                    <span style={{ flex: 1 }}>{item.label}</span>
                    {item.badge && (
                      <span
                        style={{
                          backgroundColor: "#c00",
                          color: "#fff",
                          fontSize: "11px",
                          borderRadius: "10px",
                          padding: "1px 7px",
                        }}
                      >
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
    </div>
  );
}

export default Sidebar;
