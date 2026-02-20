import { useState } from "react";
import {
  Button,
  CloseButton,
  Dialog,
  Portal,
  Text,
} from "@chakra-ui/react";
import type { RuleHeader } from "../types";
import { useRulesStore } from "../store/rulesStore";

interface CloneConfirmDialogProps {
  open: boolean;
  header: RuleHeader;
  onClose: () => void;
  onCloned: (newHeader: RuleHeader) => void;
}

export default function CloneConfirmDialog({
  open,
  header,
  onClose,
  onCloned,
}: CloneConfirmDialogProps) {
  const { cloneHeader } = useRulesStore();
  const [cloning, setCloning] = useState(false);

  const handleClone = async () => {
    setCloning(true);
    try {
      const newHeader = await cloneHeader(header.id);
      onCloned(newHeader);
    } catch {
      // error
    } finally {
      setCloning(false);
    }
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(e) => {
        if (!e.open) onClose();
      }}
      placement="center"
      size="sm"
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title fontWeight="700" color="#1A1A1A">
                Clone Rule
              </Dialog.Title>
            </Dialog.Header>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" />
            </Dialog.CloseTrigger>
            <Dialog.Body>
              <Text fontSize="sm" color="gray.600">
                Clone{" "}
                <Text as="span" fontWeight="700">
                  {header.cost_category}
                  {header.rate_category ? ` / ${header.rate_category}` : ""}
                </Text>{" "}
                v{header.version} as a new Draft?
              </Text>
              <Text fontSize="xs" color="gray.400" mt={2}>
                This will create a new draft rule (v{header.version + 1}) with
                all header fields and lines copied from the original.
              </Text>
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" onClick={onClose} size="sm">
                Cancel
              </Button>
              <Button
                bg="#FFC72C"
                color="#1A1A1A"
                fontWeight="700"
                _hover={{ bg: "#E6B327" }}
                onClick={handleClone}
                loading={cloning}
                size="sm"
              >
                Clone
              </Button>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
}
