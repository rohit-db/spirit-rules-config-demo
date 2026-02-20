import { Box, Flex, Text } from "@chakra-ui/react";
import StatusBadge from "./StatusBadge";
import type { RuleHeader } from "../types";

interface RuleHeaderCardProps {
  header: RuleHeader;
  isSelected: boolean;
  onClick: () => void;
}

function formatDateRange(start: string, end: string): string {
  const s = new Date(start + "T00:00:00");
  const e = new Date(end + "T00:00:00");
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  return `${fmt(s)} - ${fmt(e)}`;
}

export default function RuleHeaderCard({
  header,
  isSelected,
  onClick,
}: RuleHeaderCardProps) {
  return (
    <Box
      px={3}
      py={3}
      mx={2}
      mb={1}
      borderRadius="lg"
      cursor="pointer"
      bg={isSelected ? "brand.50" : "white"}
      borderWidth="2px"
      borderColor={isSelected ? "#FFC72C" : "transparent"}
      _hover={{
        bg: isSelected ? "brand.50" : "gray.50",
        borderColor: isSelected ? "#FFC72C" : "gray.200",
      }}
      transition="all 0.15s"
      onClick={onClick}
      boxShadow={isSelected ? "0 0 0 1px #FFC72C" : "sm"}
    >
      <Flex justify="space-between" align="center" mb={1}>
        <Text fontWeight="700" fontSize="sm" color="#1A1A1A" lineClamp={1}>
          {header.cost_category}
          {header.rate_category ? ` / ${header.rate_category}` : ""}
        </Text>
        <StatusBadge status={header.status} />
      </Flex>
      <Text fontSize="xs" color="gray.500" mb={1}>
        {formatDateRange(header.start_date, header.end_date)}
      </Text>
      <Flex justify="space-between" align="center">
        <Text fontSize="xs" color="gray.500">
          {header.account_group || "No group"}
        </Text>
        <Text fontSize="xs" color="gray.400" fontWeight="500">
          v{header.version}
        </Text>
      </Flex>
    </Box>
  );
}
