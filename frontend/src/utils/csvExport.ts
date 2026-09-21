/**
 * Utility to export tabular data to a downloadable CSV file.
 */
export function exportToCsv(
  filename: string,
  rows: Array<Record<string, unknown>>,
  headers?: { key: string; label: string }[]
): void {
  if (!rows || rows.length === 0) return;

  const resolvedHeaders =
    headers ||
    Object.keys(rows[0]).map((key) => ({
      key,
      label: key.replace(/_/g, ' ').toUpperCase(),
    }));

  const escapeCsvCell = (value: unknown): string => {
    if (value === null || value === undefined) return '""';
    const str = typeof value === 'object' ? JSON.stringify(value) : String(value);
    const escaped = str.replace(/"/g, '""');
    return `"${escaped}"`;
  };

  const headerLine = resolvedHeaders.map((h) => escapeCsvCell(h.label)).join(',');
  const rowLines = rows.map((row) =>
    resolvedHeaders.map((h) => escapeCsvCell(row[h.key])).join(',')
  );

  const csvContent = [headerLine, ...rowLines].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
