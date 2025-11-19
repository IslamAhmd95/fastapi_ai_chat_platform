export function formatTimestamp(dateString: string) {
  const date = new Date(dateString);

  if (isNaN(date.getTime())) return ""; // Prevent "Invalid Date"

  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}
