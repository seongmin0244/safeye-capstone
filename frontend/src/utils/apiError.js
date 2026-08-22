export function getApiErrorMessage(json, fallback = "요청을 처리하지 못했습니다.") {
  const error = json?.error;
  const details = error?.details;

  if (details?.limit) {
    const limitMB = Math.round(Number(details.limit) / (1024 * 1024));
    return `파일이 너무 큽니다. ${limitMB}MB까지 업로드할 수 있어요.`;
  }

  return error?.message ?? fallback;
}