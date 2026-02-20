import { useState } from "react";
import { Accordion, Badge, Box, Flex, Text } from "@chakra-ui/react";
import type { AuditEntry } from "../types";

interface AuditLogProps {
  entries: AuditEntry[];
}

const ACTION_COLORS: Record<string, string> = {
  create: "green",
  update: "blue",
  delete: "red",
  clone: "purple",
  status_change: "orange",
  add_lines: "teal",
  update_line: "blue",
  delete_line: "red",
  import_csv: "cyan",
};

const ACTION_LABELS: Record<string, string> = {
  create: "Created",
  update: "Updated",
  delete: "Deleted",
  clone: "Cloned",
  status_change: "Status Changed",
  add_lines: "Lines Added",
  update_line: "Line Updated",
  delete_line: "Line Deleted",
  import_csv: "CSV Imported",
};

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function JsonDisplay({ data }: { data: Record<string, unknown> | null }) {
  if (!data) return <Text fontSize="xs" color="gray.400">--</Text>;
  return (
    <Box
      as="pre"
      fontSize="xs"
      bg="gray.50"
      p={2}
      borderRadius="md"
      overflowX="auto"
      maxH="120px"
      fontFamily="mono"
      color="gray.600"
    >
      {JSON.stringify(data, null, 2)}
    </Box>
  );
}

export default function AuditLog({ entries }: AuditLogProps) {
  const [expanded, setExpanded] = useState(false);

  if (entries.length === 0) return null;

  return (
    <Box
      bg="white"
      borderRadius="lg"
      borderWidth="1px"
      borderColor="gray.200"
      overflow="hidden"
    >
      <Box
        px={5}
        py={3}
        cursor="pointer"
        onClick={() => setExpanded(!expanded)}
        _hover={{ bg: "gray.50" }}
        transition="background 0.1s"
      >
        <Flex justify="space-between" align="center">
          <Text fontSize="sm" fontWeight="700" color="#1A1A1A">
            Audit History
          </Text>
          <Flex align="center" gap={2}>
            <Text fontSize="xs" color="gray.400">
              {entries.length} {entries.length === 1 ? "entry" : "entries"}
            </Text>
            <Text fontSize="sm" color="gray.400">
              {expanded ? "\u25B2" : "\u25BC"}
            </Text>
          </Flex>
        </Flex>
      </Box>

      {expanded && (
        <Box px={5} pb={4}>
          <Accordion.Root collapsible>
            {entries.map((entry) => (
              <Accordion.Item key={entry.id} value={entry.id}>
                <Accordion.ItemTrigger
                  cursor="pointer"
                  py={2}
                  px={0}
                  _hover={{ bg: "transparent" }}
                >
                  <Flex
                    flex="1"
                    align="center"
                    gap={3}
                    fontSize="sm"
                  >
                    <Badge
                      colorPalette={ACTION_COLORS[entry.action] || "gray"}
                      size="sm"
                      variant="solid"
                      fontSize="xs"
                    >
                      {ACTION_LABELS[entry.action] || entry.action}
                    </Badge>
                    <Text fontSize="xs" color="gray.500">
                      {entry.changed_by}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      {formatTimestamp(entry.changed_at)}
                    </Text>
                  </Flex>
                  <Accordion.ItemIndicator />
                </Accordion.ItemTrigger>
                <Accordion.ItemContent>
                  <Accordion.ItemBody>
                    <Flex gap={4} direction={{ base: "column", md: "row" }}>
                      {entry.old_values && (
                        <Box flex="1">
                          <Text fontSize="xs" fontWeight="600" color="red.500" mb={1}>
                            Old Values
                          </Text>
                          <JsonDisplay data={entry.old_values} />
                        </Box>
                      )}
                      {entry.new_values && (
                        <Box flex="1">
                          <Text fontSize="xs" fontWeight="600" color="green.500" mb={1}>
                            New Values
                          </Text>
                          <JsonDisplay data={entry.new_values} />
                        </Box>
                      )}
                    </Flex>
                  </Accordion.ItemBody>
                </Accordion.ItemContent>
              </Accordion.Item>
            ))}
          </Accordion.Root>
        </Box>
      )}
    </Box>
  );
}
