import { Badge } from "@chakra-ui/react";

const STATUS_COLORS: Record<string, string> = {
  draft: "gray",
  in_review: "orange",
  approved: "green",
  archived: "blue",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  in_review: "In Review",
  approved: "Approved",
  archived: "Archived",
};

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md" | "lg";
}

export default function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  return (
    <Badge
      colorPalette={STATUS_COLORS[status] || "gray"}
      size={size}
      variant="solid"
      borderRadius="md"
      px={2}
      py={0.5}
      textTransform="capitalize"
      fontSize="xs"
      fontWeight="600"
    >
      {STATUS_LABELS[status] || status}
    </Badge>
  );
}
