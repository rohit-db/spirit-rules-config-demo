import { useState, useCallback } from "react";
import { Box, Button, Flex, Input, Text, Table } from "@chakra-ui/react";
import { LuPlus, LuTrash2 } from "react-icons/lu";
import type { RuleLine } from "../types";
import { useRulesStore } from "../store/rulesStore";

interface LinesTableProps {
  lines: RuleLine[];
  headerId: string;
  editable: boolean;
}

const STAT_TYPES = ["ASMs", "Departures", "Block_Hours", "RPMs"];

interface EditingCell {
  lineId: string;
  field: string;
}

export default function LinesTable({
  lines,
  headerId,
  editable,
}: LinesTableProps) {
  const { createLine, updateLine, deleteLine } = useRulesStore();
  const [editingCell, setEditingCell] = useState<EditingCell | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [addingRow, setAddingRow] = useState(false);
  const [newRow, setNewRow] = useState({
    account_number: "",
    account_name: "",
    stat_type: "ASMs",
    proration_rate: "",
    effective_date: "",
    notes: "",
  });

  const startEdit = useCallback(
    (lineId: string, field: string, currentValue: string) => {
      if (!editable) return;
      setEditingCell({ lineId, field });
      setEditValue(currentValue);
    },
    [editable]
  );

  const commitEdit = useCallback(async () => {
    if (!editingCell) return;
    const { lineId, field } = editingCell;

    // Find original line to check if value actually changed
    const originalLine = lines.find((l) => l.id === lineId);
    if (!originalLine) return;

    const originalValue = String(
      originalLine[field as keyof RuleLine] ?? ""
    );

    if (editValue !== originalValue) {
      let value: string | number | null = editValue;
      if (field === "proration_rate") {
        value = parseFloat(editValue) || 0;
      }
      if (
        (field === "account_name" ||
          field === "effective_date" ||
          field === "notes") &&
        editValue === ""
      ) {
        value = null;
      }
      await updateLine(headerId, lineId, { [field]: value } as Partial<RuleLine>);
    }

    setEditingCell(null);
    setEditValue("");
  }, [editingCell, editValue, headerId, lines, updateLine]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      commitEdit();
    } else if (e.key === "Escape") {
      setEditingCell(null);
      setEditValue("");
    } else if (e.key === "Tab") {
      e.preventDefault();
      commitEdit();
    }
  };

  const handleAddRow = async () => {
    if (!newRow.account_number || !newRow.stat_type || !newRow.proration_rate)
      return;

    await createLine(headerId, {
      account_number: newRow.account_number,
      account_name: newRow.account_name || null,
      stat_type: newRow.stat_type,
      proration_rate: parseFloat(newRow.proration_rate),
      effective_date: newRow.effective_date || null,
      notes: newRow.notes || null,
      sort_order: lines.length,
    } as Partial<RuleLine>);

    setNewRow({
      account_number: "",
      account_name: "",
      stat_type: "ASMs",
      proration_rate: "",
      effective_date: "",
      notes: "",
    });
    setAddingRow(false);
  };

  const renderCell = (
    line: RuleLine,
    field: string,
    value: string | number | null | undefined,
    width?: string
  ) => {
    const isEditing =
      editingCell?.lineId === line.id && editingCell?.field === field;

    if (isEditing) {
      if (field === "stat_type") {
        return (
          <select
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={handleKeyDown}
            autoFocus
            style={{
              padding: "2px 6px",
              fontSize: "13px",
              border: "2px solid #FFC72C",
              borderRadius: "4px",
              width: "100%",
              outline: "none",
            }}
          >
            {STAT_TYPES.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        );
      }

      return (
        <Input
          size="sm"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={commitEdit}
          onKeyDown={handleKeyDown}
          autoFocus
          borderColor="#FFC72C"
          borderWidth="2px"
          _focus={{ borderColor: "#FFC72C", boxShadow: "0 0 0 1px #FFC72C" }}
          px={1}
          py={0}
          h="28px"
          fontSize="13px"
          type={field === "proration_rate" ? "number" : field === "effective_date" ? "date" : "text"}
          step={field === "proration_rate" ? "0.01" : undefined}
          width={width}
        />
      );
    }

    return (
      <Text
        fontSize="13px"
        cursor={editable ? "pointer" : "default"}
        px={1}
        py={0.5}
        borderRadius="sm"
        _hover={editable ? { bg: "brand.50" } : {}}
        onClick={() => startEdit(line.id, field, String(value ?? ""))}
        lineClamp={1}
      >
        {field === "proration_rate" && value !== null && value !== undefined
          ? Number(value).toFixed(4)
          : value ?? "--"}
      </Text>
    );
  };

  // Compute proration sum
  const prorationSum = lines.reduce((acc, l) => acc + l.proration_rate, 0);

  return (
    <Box
      bg="white"
      borderRadius="lg"
      borderWidth="1px"
      borderColor="gray.200"
      mb={4}
      overflow="hidden"
    >
      <Flex
        justify="space-between"
        align="center"
        px={5}
        py={3}
        borderBottomWidth="1px"
        borderColor="gray.100"
      >
        <Flex align="center" gap={3}>
          <Text fontSize="sm" fontWeight="700" color="#1A1A1A">
            Rule Lines
          </Text>
          <Text fontSize="xs" color="gray.400">
            {lines.length} {lines.length === 1 ? "line" : "lines"}
          </Text>
          <Text
            fontSize="xs"
            fontWeight="600"
            color={Math.abs(prorationSum - 1.0) < 0.005 ? "green.600" : "orange.500"}
          >
            Sum: {prorationSum.toFixed(4)}
          </Text>
        </Flex>
        {editable && (
          <Button
            size="xs"
            bg="#FFC72C"
            color="#1A1A1A"
            fontWeight="600"
            _hover={{ bg: "#E6B327" }}
            onClick={() => setAddingRow(true)}
          >
            <LuPlus />
            Add Row
          </Button>
        )}
      </Flex>

      <Box overflowX="auto">
        <Table.Root size="sm" variant="outline">
          <Table.Header>
            <Table.Row bg="gray.50">
              <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600" w="110px">
                Account #
              </Table.ColumnHeader>
              <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600" w="180px">
                Account Name
              </Table.ColumnHeader>
              <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600" w="120px">
                Stat Type
              </Table.ColumnHeader>
              <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600" w="110px" textAlign="end">
                Proration Rate
              </Table.ColumnHeader>
              <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600" w="120px">
                Effective Date
              </Table.ColumnHeader>
              <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600">
                Notes
              </Table.ColumnHeader>
              {editable && (
                <Table.ColumnHeader fontSize="xs" fontWeight="600" color="gray.600" w="60px" textAlign="center">
                  Actions
                </Table.ColumnHeader>
              )}
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {lines.map((line) => (
              <Table.Row
                key={line.id}
                _hover={{ bg: "gray.50" }}
                transition="background 0.1s"
              >
                <Table.Cell>
                  {renderCell(line, "account_number", line.account_number)}
                </Table.Cell>
                <Table.Cell>
                  {renderCell(line, "account_name", line.account_name)}
                </Table.Cell>
                <Table.Cell>
                  {renderCell(line, "stat_type", line.stat_type)}
                </Table.Cell>
                <Table.Cell textAlign="end">
                  {renderCell(line, "proration_rate", line.proration_rate)}
                </Table.Cell>
                <Table.Cell>
                  {renderCell(line, "effective_date", line.effective_date)}
                </Table.Cell>
                <Table.Cell>
                  {renderCell(line, "notes", line.notes)}
                </Table.Cell>
                {editable && (
                  <Table.Cell textAlign="center">
                    <Button
                      size="xs"
                      variant="ghost"
                      colorPalette="red"
                      onClick={() => deleteLine(headerId, line.id)}
                    >
                      <LuTrash2 />
                    </Button>
                  </Table.Cell>
                )}
              </Table.Row>
            ))}

            {/* Add row form */}
            {addingRow && editable && (
              <Table.Row bg="brand.50">
                <Table.Cell>
                  <Input
                    size="sm"
                    placeholder="5100-XX"
                    value={newRow.account_number}
                    onChange={(e) =>
                      setNewRow({ ...newRow, account_number: e.target.value })
                    }
                    fontSize="13px"
                    h="28px"
                    px={1}
                  />
                </Table.Cell>
                <Table.Cell>
                  <Input
                    size="sm"
                    placeholder="Name"
                    value={newRow.account_name}
                    onChange={(e) =>
                      setNewRow({ ...newRow, account_name: e.target.value })
                    }
                    fontSize="13px"
                    h="28px"
                    px={1}
                  />
                </Table.Cell>
                <Table.Cell>
                  <select
                    value={newRow.stat_type}
                    onChange={(e) =>
                      setNewRow({ ...newRow, stat_type: e.target.value })
                    }
                    style={{
                      padding: "2px 6px",
                      fontSize: "13px",
                      border: "1px solid #e2e8f0",
                      borderRadius: "4px",
                      width: "100%",
                    }}
                  >
                    {STAT_TYPES.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </Table.Cell>
                <Table.Cell>
                  <Input
                    size="sm"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={newRow.proration_rate}
                    onChange={(e) =>
                      setNewRow({ ...newRow, proration_rate: e.target.value })
                    }
                    fontSize="13px"
                    h="28px"
                    px={1}
                  />
                </Table.Cell>
                <Table.Cell>
                  <Input
                    size="sm"
                    type="date"
                    value={newRow.effective_date}
                    onChange={(e) =>
                      setNewRow({ ...newRow, effective_date: e.target.value })
                    }
                    fontSize="13px"
                    h="28px"
                    px={1}
                  />
                </Table.Cell>
                <Table.Cell>
                  <Input
                    size="sm"
                    placeholder="Notes"
                    value={newRow.notes}
                    onChange={(e) =>
                      setNewRow({ ...newRow, notes: e.target.value })
                    }
                    fontSize="13px"
                    h="28px"
                    px={1}
                  />
                </Table.Cell>
                <Table.Cell>
                  <Flex gap={1} justify="center">
                    <Button
                      size="xs"
                      bg="#FFC72C"
                      color="#1A1A1A"
                      _hover={{ bg: "#E6B327" }}
                      onClick={handleAddRow}
                    >
                      Add
                    </Button>
                    <Button
                      size="xs"
                      variant="ghost"
                      onClick={() => setAddingRow(false)}
                    >
                      X
                    </Button>
                  </Flex>
                </Table.Cell>
              </Table.Row>
            )}

            {lines.length === 0 && !addingRow && (
              <Table.Row>
                <Table.Cell colSpan={editable ? 7 : 6}>
                  <Flex justify="center" py={6}>
                    <Text color="gray.400" fontSize="sm">
                      No lines configured. {editable ? 'Click "Add Row" to begin.' : ""}
                    </Text>
                  </Flex>
                </Table.Cell>
              </Table.Row>
            )}
          </Table.Body>
        </Table.Root>
      </Box>
    </Box>
  );
}
