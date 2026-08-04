function Sidebar({ currentPage, onNavigate }) {
  const menuItems = [
    { key: "photo-upload", label: "사진 업로드" },
    { key: "stats", label: "통계 리포트" },
  ];

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
      {menuItems.map((item) => (
        <button
          key={item.key}
          onClick={() => onNavigate(item.key)}
          style={{
            display: "block",
            width: "100%",
            textAlign: "left",
            padding: "10px 12px",
            marginBottom: "6px",
            backgroundColor: currentPage == item.key ? "#333" : "transparent",
            color: currentPage === item.key ? "#fff" : "#333",
            cursor: "pointer",
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

export default Sidebar;
