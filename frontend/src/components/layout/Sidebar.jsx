import { NavLink } from "react-router-dom";
import { MENU_ITEMS } from "../../constants/menu";

function Sidebar() {
  return (
    <div
      style={{
        width: "180px",
        borderRight: "1px solid #eee",
        padding: "16px",
        minHeight: "100vh",
      }}
    >
      <h3 style={{ marginBottom: "16px" }}>safEYE</h3>
      {MENU_ITEMS.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          style={({ isActive }) => ({
            display: "block",
            padding: "10px 12px",
            marginBottom: "6px",
            borderRadius: "6px",
            textDecoration: "none",
            backgroundColor: isActive ? "#333" : "transparent",
            color: isActive ? "#fff" : "#333",
          })}
        >
          {item.label}
        </NavLink>
      ))}
    </div>
  );
}

export default Sidebar;

//NavLink: 지금 이 링크가 현재 화면인지 자동으로 알려주는 라우터 전용 컴포넌트
//style={({ isActive }) => ({...})}:
// isActive는 "지금 메뉴가 선택된 상태인지"를 라우터가 자동으로 계산해서 넘겨줌
