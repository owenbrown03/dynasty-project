export const ROOKIE_DRAFT_ROLLOVER_MONTH = 5;
export const ROOKIE_DRAFT_ROLLOVER_DAY = 1;

export function getValidSleeperPickYears(
  now = new Date(),
): string[] {
  const currentYear = now.getFullYear();
  return Array.from(
    {
      length: 4,
    },
    (_, index) => String(currentYear + index),
  );
}
