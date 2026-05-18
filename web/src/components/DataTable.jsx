import React, { useEffect, useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ChevronsUpDown } from 'lucide-react';

import EmptyState from './EmptyState.jsx';
import LoadingSpinner from './LoadingSpinner.jsx';
import { Button } from './ui/button.jsx';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select.jsx';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table.jsx';
import { cn } from '@/lib/cn';
import { filterRows, getCellValue, paginateRows, sortRows } from './DataTable.js';

const getRowKey = (rowKey, record, index) => {
  if (typeof rowKey === 'function') return rowKey(record, index);
  if (typeof rowKey === 'string') return record?.[rowKey] ?? index;
  return record?.id ?? record?.key ?? index;
};

const getNextOrder = (currentOrder) => {
  if (!currentOrder) return 'desc';
  if (currentOrder === 'desc') return 'asc';
  return '';
};

const SortIcon = ({ order }) => {
  if (order === 'asc') return <ArrowUp data-icon="inline-end" />;
  if (order === 'desc') return <ArrowDown data-icon="inline-end" />;
  return <ChevronsUpDown data-icon="inline-end" />;
};

const ResizableHandle = ({ onResize }) => {
  const rafRef = React.useRef(null);
  const pendingWidthRef = React.useRef(null);

  const handleMouseDown = (event) => {
    event.preventDefault();
    event.stopPropagation();

    const startX = event.clientX;
    const startWidth = event.currentTarget.parentElement?.getBoundingClientRect().width || 0;

    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (moveEvent) => {
      pendingWidthRef.current = startWidth + moveEvent.clientX - startX;
      if (rafRef.current == null) {
        rafRef.current = requestAnimationFrame(() => {
          onResize?.(pendingWidthRef.current);
          rafRef.current = null;
        });
      }
    };

    const handleMouseUp = () => {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      // 确保最后一帧被渲染
      if (rafRef.current != null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      onResize?.(pendingWidthRef.current);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <span
      role="separator"
      aria-orientation="vertical"
      className="absolute right-0 top-0 h-full w-2 cursor-col-resize select-none"
      onMouseDown={handleMouseDown}
    />
  );
};

const HeaderCell = ({ column, width, sortState, onSort, onFilter, onResize }) => {
  const isSorted = sortState?.key === column.key;
  const title = typeof column.title === 'function' ? column.title() : column.title;

  return (
    <TableHead
      className="relative"
      style={width ? { width, minWidth: width } : undefined}
    >
      <div className="flex min-w-0 flex-col gap-1.5">
        <div className="flex min-w-0 items-center">
          {column.sorter ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto min-w-0 justify-start px-0 text-sm font-semibold"
              onClick={() => onSort(column)}
            >
              <span className="truncate">{title}</span>
              <SortIcon order={isSorted ? sortState.order : ''} />
            </Button>
          ) : (
            <span className="truncate text-sm font-semibold">{title}</span>
          )}
        </div>
        {Array.isArray(column.filters) && column.filters.length ? (
          <Select
            value={column.filterValue || '__all__'}
            onValueChange={(value) => onFilter(column, value === '__all__' ? '' : value)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="全部" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="__all__">全部</SelectItem>
                {column.filters.map((filter) => (
                  <SelectItem key={String(filter.value)} value={String(filter.value)}>
                    {filter.text}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        ) : null}
      </div>
      {onResize ? <ResizableHandle onResize={onResize} /> : null}
    </TableHead>
  );
};

const DataTable = ({
  columns = [],
  data = [],
  rowKey,
  loading = false,
  error = '',
  emptyDescription = '暂无数据',
  pagination = false,
  className,
}) => {
  const [sortState, setSortState] = useState(() => {
    const defaultColumn = columns.find((column) => column.defaultSortOrder);
    if (!defaultColumn) return {};
    return {
      key: defaultColumn.key,
      sorter: defaultColumn.sorter,
      order: defaultColumn.defaultSortOrder === 'ascend' ? 'asc' : 'desc',
    };
  });
  const [filterState, setFilterState] = useState({});
  const [page, setPage] = useState(1);
  const [columnWidths, setColumnWidths] = useState(() =>
    Object.fromEntries(columns.filter((column) => column.width).map((column) => [column.key, column.width])),
  );

  useEffect(() => {
    setPage(1);
  }, [data, filterState, sortState]);

  const columnsWithFilters = useMemo(
    () =>
      columns.map((column) => ({
        ...column,
        filterValue: filterState[column.key]?.value || '',
      })),
    [columns, filterState],
  );

  const processedRows = useMemo(() => {
    const filtered = filterRows(data, filterState);
    return sortRows(filtered, sortState);
  }, [data, filterState, sortState]);

  const pageSize = pagination?.pageSize || (pagination ? 10 : null);
  const paginated = useMemo(
    () => paginateRows(processedRows, { page, pageSize }),
    [page, pageSize, processedRows],
  );

  const visibleRows = pageSize ? paginated.rows : processedRows;

  const handleSort = (column) => {
    const order = sortState.key === column.key ? getNextOrder(sortState.order) : 'desc';
    setSortState(order ? { key: column.key, sorter: column.sorter, order } : {});
  };

  const handleFilter = (column, value) => {
    setFilterState((previous) => {
      const next = { ...previous };
      if (!value) {
        delete next[column.key];
      } else {
        next[column.key] = {
          value,
          onFilter: column.onFilter || ((filterValue, record) => String(getCellValue(record, column.dataIndex)) === String(filterValue)),
        };
      }
      return next;
    });
  };

  const handleResize = (column) => (nextWidth) => {
    const width = Math.max(80, Math.round(nextWidth));
    setColumnWidths((previous) => ({ ...previous, [column.key]: width }));
    column.onResize?.(width);
  };

  if (loading) {
    return (
      <div className="flex min-h-32 items-center justify-center">
        <LoadingSpinner text="正在加载表格数据..." />
      </div>
    );
  }

  if (error) {
    return <EmptyState title="数据加载失败" description={error} icon="!" />;
  }

  if (!visibleRows.length) {
    return <EmptyState title="暂无数据" description={emptyDescription} />;
  }

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            {columnsWithFilters.map((column) => (
              <HeaderCell
                key={column.key}
                column={column}
                width={columnWidths[column.key]}
                sortState={sortState}
                onSort={handleSort}
                onFilter={handleFilter}
                onResize={column.resizable === false ? null : handleResize(column)}
              />
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {visibleRows.map((record, rowIndex) => (
            <TableRow key={getRowKey(rowKey, record, rowIndex)}>
              {columns.map((column) => {
                const value = getCellValue(record, column.dataIndex);
                return (
                  <TableCell key={column.key} style={columnWidths[column.key] ? { width: columnWidths[column.key] } : undefined}>
                    {column.render ? column.render(value, record, rowIndex) : value}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {pageSize && paginated.pageCount > 1 ? (
        <div className="flex items-center justify-end gap-2 px-1">
          <Button variant="outline" size="sm" disabled={paginated.page <= 1} onClick={() => setPage((value) => value - 1)}>
            上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            {paginated.page} / {paginated.pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={paginated.page >= paginated.pageCount}
            onClick={() => setPage((value) => value + 1)}
          >
            下一页
          </Button>
        </div>
      ) : null}
    </div>
  );
};

export default DataTable;
