export const filterRows = (rows, filters = {}) => {
  const sourceRows = Array.isArray(rows) ? rows : [];
  const activeFilters = Object.values(filters).filter((filter) => filter?.value !== undefined && filter?.value !== '');

  if (!activeFilters.length) return sourceRows;

  return sourceRows.filter((row) =>
    activeFilters.every((filter) => {
      if (typeof filter.onFilter === 'function') {
        return filter.onFilter(filter.value, row);
      }
      return true;
    }),
  );
};

export const sortRows = (rows, sortState = {}) => {
  const sourceRows = Array.isArray(rows) ? rows : [];
  const { sorter, order } = sortState;

  if (typeof sorter !== 'function' || !order) return sourceRows;

  const direction = order === 'desc' ? -1 : 1;
  return [...sourceRows].sort((a, b) => direction * sorter(a, b));
};

export const paginateRows = (rows, { page = 1, pageSize } = {}) => {
  const sourceRows = Array.isArray(rows) ? rows : [];
  if (!pageSize) {
    return { rows: sourceRows, page: 1, pageCount: 1 };
  }

  const pageCount = Math.max(1, Math.ceil(sourceRows.length / pageSize));
  const safePage = Math.min(Math.max(1, page), pageCount);
  const start = (safePage - 1) * pageSize;

  return {
    rows: sourceRows.slice(start, start + pageSize),
    page: safePage,
    pageCount,
  };
};

export const getCellValue = (record, dataIndex) => {
  if (!dataIndex) return undefined;
  if (Array.isArray(dataIndex)) {
    return dataIndex.reduce((value, key) => value?.[key], record);
  }
  return record?.[dataIndex];
};
