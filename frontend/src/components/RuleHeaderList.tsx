import { useEffect, useState } from "react";
import { Box, Button, Flex, Text, Spinner } from "@chakra-ui/react";
import { LuPlus } from "react-icons/lu";
import { useRulesStore } from "../store/rulesStore";
import FilterBar from "./FilterBar";
import RuleHeaderCard from "./RuleHeaderCard";
import NewRuleDialog from "./NewRuleDialog";

export default function RuleHeaderList() {
  const { headers, selectedHeaderId, loading, fetchHeaders, selectHeader } =
    useRulesStore();
  const [showNewRule, setShowNewRule] = useState(false);

  useEffect(() => {
    fetchHeaders();
  }, [fetchHeaders]);

  return (
    <Flex
      direction="column"
      h="100vh"
      w="380px"
      minW="380px"
      borderRightWidth="1px"
      borderColor="gray.200"
      bg="gray.50"
    >
      {/* Header */}
      <Box
        px={4}
        py={3}
        bg="#1A1A1A"
        borderBottomWidth="3px"
        borderColor="#FFC72C"
      >
        <Text
          fontSize="md"
          fontWeight="800"
          color="white"
          letterSpacing="tight"
        >
          Spirit Airlines
        </Text>
        <Text fontSize="xs" color="#FFC72C" fontWeight="600" mt={-0.5}>
          Rules Configuration
        </Text>
      </Box>

      {/* New Rule button */}
      <Box px={3} pt={3} pb={1}>
        <Button
          size="sm"
          w="100%"
          bg="#FFC72C"
          color="#1A1A1A"
          fontWeight="700"
          _hover={{ bg: "#E6B327" }}
          onClick={() => setShowNewRule(true)}
        >
          <LuPlus />
          New Rule
        </Button>
      </Box>

      {/* Filters */}
      <FilterBar />

      {/* List */}
      <Box flex="1" overflowY="auto" pb={4}>
        {loading ? (
          <Flex justify="center" align="center" h="100px">
            <Spinner size="md" color="#FFC72C" />
          </Flex>
        ) : headers.length === 0 ? (
          <Flex justify="center" align="center" h="100px">
            <Text color="gray.400" fontSize="sm">
              No rules found
            </Text>
          </Flex>
        ) : (
          headers.map((header) => (
            <RuleHeaderCard
              key={header.id}
              header={header}
              isSelected={selectedHeaderId === header.id}
              onClick={() => selectHeader(header.id)}
            />
          ))
        )}
      </Box>

      {/* New Rule Dialog */}
      <NewRuleDialog
        open={showNewRule}
        onClose={() => setShowNewRule(false)}
      />
    </Flex>
  );
}
