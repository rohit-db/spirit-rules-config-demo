import { Box, Flex, Text } from "@chakra-ui/react";
import { useRulesStore } from "../store/rulesStore";
import HeaderDetailCard from "./HeaderDetailCard";
import LinesTable from "./LinesTable";
import ActionBar from "./ActionBar";
import AuditLog from "./AuditLog";

export default function RuleDetail() {
  const { headers, selectedHeaderId, lines, auditLog } = useRulesStore();

  if (!selectedHeaderId) {
    return (
      <Flex
        flex="1"
        align="center"
        justify="center"
        bg="gray.50"
        direction="column"
        gap={2}
      >
        <Text fontSize="xl" fontWeight="600" color="gray.300">
          Select a rule to view details
        </Text>
        <Text fontSize="sm" color="gray.300">
          Choose from the list on the left
        </Text>
      </Flex>
    );
  }

  const header = headers.find((h) => h.id === selectedHeaderId);

  if (!header) {
    return (
      <Flex flex="1" align="center" justify="center" bg="gray.50">
        <Text color="gray.400">Rule not found</Text>
      </Flex>
    );
  }

  const editable = header.status === "draft";

  return (
    <Box flex="1" h="100vh" overflowY="auto" bg="gray.50" p={6}>
      <HeaderDetailCard header={header} />
      <ActionBar header={header} />
      <LinesTable lines={lines} headerId={header.id} editable={editable} />
      <AuditLog entries={auditLog} />
    </Box>
  );
}
