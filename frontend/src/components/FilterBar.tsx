import { Flex, Input } from "@chakra-ui/react";
import { useRulesStore } from "../store/rulesStore";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "draft", label: "Draft" },
  { value: "in_review", label: "In Review" },
  { value: "approved", label: "Approved" },
  { value: "archived", label: "Archived" },
];

const COST_CATEGORY_OPTIONS = [
  { value: "", label: "All Categories" },
  { value: "Fuel", label: "Fuel" },
  { value: "Crew", label: "Crew" },
  { value: "Maintenance", label: "Maintenance" },
];

export default function FilterBar() {
  const { filters, setFilters } = useRulesStore();

  return (
    <Flex direction="column" gap={2} px={3} py={2}>
      <select
        value={filters.status}
        onChange={(e) => setFilters({ status: e.target.value })}
        style={{
          padding: "6px 10px",
          borderRadius: "6px",
          border: "1px solid #e2e8f0",
          fontSize: "13px",
          backgroundColor: "white",
          color: "#333",
          cursor: "pointer",
        }}
      >
        {STATUS_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <select
        value={filters.cost_category}
        onChange={(e) => setFilters({ cost_category: e.target.value })}
        style={{
          padding: "6px 10px",
          borderRadius: "6px",
          border: "1px solid #e2e8f0",
          fontSize: "13px",
          backgroundColor: "white",
          color: "#333",
          cursor: "pointer",
        }}
      >
        {COST_CATEGORY_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <Input
        placeholder="Search rules..."
        size="sm"
        value={filters.search}
        onChange={(e) => setFilters({ search: e.target.value })}
        borderRadius="md"
        bg="white"
      />
    </Flex>
  );
}
