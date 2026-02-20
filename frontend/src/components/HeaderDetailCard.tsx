import { useState } from "react";
import {
  Box,
  Button,
  Flex,
  Input,
  Text,
} from "@chakra-ui/react";
import { LuPencil, LuX, LuCheck } from "react-icons/lu";
import StatusBadge from "./StatusBadge";
import type { RuleHeader } from "../types";
import { useRulesStore } from "../store/rulesStore";

interface HeaderDetailCardProps {
  header: RuleHeader;
}

export default function HeaderDetailCard({ header }: HeaderDetailCardProps) {
  const { updateHeader } = useRulesStore();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<RuleHeader>>({});
  const isDraft = header.status === "draft";

  const startEditing = () => {
    setForm({
      start_date: header.start_date,
      end_date: header.end_date,
      cost_category: header.cost_category,
      rate_category: header.rate_category || "",
      category: header.category || "",
      account_group: header.account_group || "",
      fixed_variable_pct_split: header.fixed_variable_pct_split,
      fixed_variable_type: header.fixed_variable_type || "",
    });
    setEditing(true);
  };

  const cancelEditing = () => {
    setEditing(false);
    setForm({});
  };

  const saveEditing = async () => {
    try {
      const updates: Record<string, unknown> = {};
      if (form.start_date && form.start_date !== header.start_date)
        updates.start_date = form.start_date;
      if (form.end_date && form.end_date !== header.end_date)
        updates.end_date = form.end_date;
      if (form.cost_category && form.cost_category !== header.cost_category)
        updates.cost_category = form.cost_category;
      if (form.rate_category !== undefined && form.rate_category !== header.rate_category)
        updates.rate_category = form.rate_category || null;
      if (form.category !== undefined && form.category !== header.category)
        updates.category = form.category || null;
      if (form.account_group !== undefined && form.account_group !== header.account_group)
        updates.account_group = form.account_group || null;
      if (
        form.fixed_variable_pct_split !== undefined &&
        form.fixed_variable_pct_split !== header.fixed_variable_pct_split
      )
        updates.fixed_variable_pct_split = form.fixed_variable_pct_split;
      if (
        form.fixed_variable_type !== undefined &&
        form.fixed_variable_type !== header.fixed_variable_type
      )
        updates.fixed_variable_type = form.fixed_variable_type || null;

      if (Object.keys(updates).length > 0) {
        await updateHeader(header.id, updates as Partial<RuleHeader>);
      }
      setEditing(false);
    } catch {
      // Error handling - stay in edit mode
    }
  };

  const updateField = (field: string, value: string | number | null) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const renderField = (
    label: string,
    field: keyof RuleHeader,
    value: string | number | boolean | null | undefined,
    type: "text" | "date" | "number" = "text"
  ) => {
    if (editing) {
      return (
        <Box>
          <Text fontSize="xs" color="gray.500" fontWeight="500" mb={0.5}>
            {label}
          </Text>
          <Input
            size="sm"
            type={type}
            value={String(form[field] ?? "")}
            onChange={(e) =>
              updateField(
                field,
                type === "number" ? parseFloat(e.target.value) || null : e.target.value
              )
            }
            borderRadius="md"
            bg="white"
          />
        </Box>
      );
    }

    return (
      <Box>
        <Text fontSize="xs" color="gray.500" fontWeight="500" mb={0.5}>
          {label}
        </Text>
        <Text fontSize="sm" fontWeight="500" color="#1A1A1A">
          {value === null || value === undefined || value === ""
            ? "--"
            : typeof value === "boolean"
            ? value
              ? "Yes"
              : "No"
            : String(value)}
        </Text>
      </Box>
    );
  };

  return (
    <Box bg="white" borderRadius="lg" borderWidth="1px" borderColor="gray.200" p={5} mb={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Flex align="center" gap={3}>
          <Text fontSize="lg" fontWeight="700" color="#1A1A1A">
            {header.cost_category}
            {header.rate_category ? ` / ${header.rate_category}` : ""}
          </Text>
          <StatusBadge status={header.status} size="md" />
          <Text fontSize="sm" color="gray.400" fontWeight="500">
            v{header.version}
          </Text>
        </Flex>
        {isDraft && !editing && (
          <Button
            size="sm"
            variant="outline"
            onClick={startEditing}
          >
            <LuPencil />
            Edit
          </Button>
        )}
        {editing && (
          <Flex gap={2}>
            <Button size="sm" bg="#FFC72C" color="#1A1A1A" _hover={{ bg: "#E6B327" }} onClick={saveEditing}>
              <LuCheck />
              Save
            </Button>
            <Button size="sm" variant="outline" onClick={cancelEditing}>
              <LuX />
              Cancel
            </Button>
          </Flex>
        )}
      </Flex>

      <Box
        display="grid"
        gridTemplateColumns="repeat(3, 1fr)"
        gap={4}
      >
        {renderField("Start Date", "start_date", header.start_date, "date")}
        {renderField("End Date", "end_date", header.end_date, "date")}
        {renderField("Cost Category", "cost_category", header.cost_category)}
        {renderField("Rate Category", "rate_category", header.rate_category)}
        {renderField("Category", "category", header.category)}
        {renderField("Account Group", "account_group", header.account_group)}
        {renderField(
          "Fixed/Variable % Split",
          "fixed_variable_pct_split",
          header.fixed_variable_pct_split,
          "number"
        )}
        {renderField(
          "Fixed/Variable Type",
          "fixed_variable_type",
          header.fixed_variable_type
        )}
        <Box>
          <Text fontSize="xs" color="gray.500" fontWeight="500" mb={0.5}>
            Group By Cost Center
          </Text>
          <Text fontSize="sm" fontWeight="500" color="#1A1A1A">
            {header.groupby_costcenter ? "Yes" : "No"}
          </Text>
        </Box>
        <Box>
          <Text fontSize="xs" color="gray.500" fontWeight="500" mb={0.5}>
            Group By Account
          </Text>
          <Text fontSize="sm" fontWeight="500" color="#1A1A1A">
            {header.groupby_account ? "Yes" : "No"}
          </Text>
        </Box>
        <Box>
          <Text fontSize="xs" color="gray.500" fontWeight="500" mb={0.5}>
            Created By
          </Text>
          <Text fontSize="sm" fontWeight="500" color="#1A1A1A">
            {header.created_by}
          </Text>
        </Box>
      </Box>
    </Box>
  );
}
