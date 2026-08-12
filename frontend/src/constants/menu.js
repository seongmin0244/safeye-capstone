import {
  LayoutDashboard,
  Camera,
  Video,
  ClipboardList,
  Scale,
  BarChart3,
  Settings,
} from "lucide-react";

export const MENU_GROUPS = [
  {
    label: "MAIN",
    items: [
      { to: "/", label: "대시보드", icon: LayoutDashboard, end: true },
      { to: "/analyze/image", label: "사진 분석", icon: Camera },
      { to: "/analyze/video", label: "영상 분석", icon: Video },
      { to: "/history", label: "분석 이력", icon: ClipboardList },
    ],
  },
  {
    label: "COMPLIANCE",
    items: [
      { to: "/compliance", label: "9대 의무 점검", icon: Scale, badge: 3 }, //3은 프로토 타입 임시 값
      { to: "/report", label: "리포트", icon: BarChart3 },
    ],
  },
  {
    label: "SYSTEM",
    items: [{ to: "/settings", label: "설정", icon: Settings }],
  },
];

export const SITES = [
  //이후에 sites.js로 분리할 수도
  { id: "a", name: "A현장 · 강남 오피스텔" },
  { id: "b", name: "B현장 · 판교 데이터센터" },
  { id: "c", name: "C현장 · 세종 아파트" },
];

const PAGE_META = {
  "/": { title: "대시보드", desc: "현장 안전 현황을 한눈에 확인하세요" },
  "/analyze/image": {
    title: "사진 분석",
    desc: "현장 사진을 업로드하면 AI가 위험 요소를 자동으로 감지합니다",
  },
  "/analyze/video": {
    title: "영상 분석",
    desc: "영상 속 위험 구간을 타임라인으로 확인하세요",
  },
  "/history": {
    title: "분석 이력",
    desc: "과거 분석 결과를 검색하고 관리합니다",
  },
  "/compliance": {
    title: "중대재해처벌법 9대 의무 점검",
    desc: "시행령 제4조 안전보건 확보의무 이행 현황",
  },
  "/report": {
    title: "리포트",
    desc: "안전점검 보고서를 생성하고 다운로드합니다",
  },
  "/settings": { title: "설정", desc: "현장 정보와 감지 항목을 관리합니다" },
};

export function getPageMeta(pathname) {
  if (PAGE_META[pathname]) return PAGE_META[pathname];
  const key = Object.keys(PAGE_META)
    .filter((k) => k !== "/" && pathname.startsWith(k))
    .sort((a, b) => b.length - a.length)[0];
  return key ? PAGE_META[key] : { title: "Safeye", desc: "" };
}
