import { useRef, useState } from "react";
import {
  Box,
  Button,
  CloseButton,
  Dialog,
  Flex,
  Portal,
  Text,
} from "@chakra-ui/react";
import { LuUpload } from "react-icons/lu";
import { useRulesStore } from "../store/rulesStore";

interface ImportDialogProps {
  open: boolean;
  headerId: string;
  onClose: () => void;
}

export default function ImportDialog({
  open,
  headerId,
  onClose,
}: ImportDialogProps) {
  const { importCSV } = useRulesStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<{
    imported: number;
    errors: { row: number; error: string }[];
  } | null>(null);

  const handleClose = () => {
    setFile(null);
    setResult(null);
    onClose();
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    try {
      const res = await importCSV(headerId, file);
      setResult(res);
    } catch {
      setResult({ imported: 0, errors: [{ row: 0, error: "Import failed" }] });
    } finally {
      setImporting(false);
    }
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(e) => {
        if (!e.open) handleClose();
      }}
      placement="center"
      size="md"
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title fontWeight="700" color="#1A1A1A">
                Import CSV
              </Dialog.Title>
            </Dialog.Header>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" />
            </Dialog.CloseTrigger>
            <Dialog.Body>
              {!result ? (
                <>
                  <Text fontSize="sm" color="gray.600" mb={3}>
                    Upload a CSV file with columns: account_number,
                    account_name, stat_type, proration_rate, effective_date,
                    notes
                  </Text>

                  <Flex
                    direction="column"
                    align="center"
                    justify="center"
                    border="2px dashed"
                    borderColor="gray.300"
                    borderRadius="lg"
                    py={8}
                    px={4}
                    cursor="pointer"
                    _hover={{ borderColor: "#FFC72C", bg: "brand.50" }}
                    transition="all 0.15s"
                    onClick={() => fileRef.current?.click()}
                  >
                    <LuUpload size={24} color="#999" />
                    <Text fontSize="sm" color="gray.500" mt={2}>
                      {file
                        ? file.name
                        : "Click to select a CSV file"}
                    </Text>
                    <input
                      ref={fileRef}
                      type="file"
                      accept=".csv"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) setFile(f);
                      }}
                    />
                  </Flex>
                </>
              ) : (
                <Box>
                  <Text
                    fontSize="sm"
                    fontWeight="600"
                    color="green.600"
                    mb={2}
                  >
                    Imported {result.imported} lines successfully.
                  </Text>
                  {result.errors.length > 0 && (
                    <Box>
                      <Text
                        fontSize="sm"
                        fontWeight="600"
                        color="red.500"
                        mb={1}
                      >
                        {result.errors.length} errors:
                      </Text>
                      <Box
                        maxH="120px"
                        overflowY="auto"
                        bg="red.50"
                        p={2}
                        borderRadius="md"
                        fontSize="xs"
                      >
                        {result.errors.map((err, i) => (
                          <Text key={i} color="red.600">
                            Row {err.row}: {err.error}
                          </Text>
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" onClick={handleClose} size="sm">
                {result ? "Close" : "Cancel"}
              </Button>
              {!result && (
                <Button
                  bg="#FFC72C"
                  color="#1A1A1A"
                  fontWeight="700"
                  _hover={{ bg: "#E6B327" }}
                  onClick={handleImport}
                  loading={importing}
                  disabled={!file}
                  size="sm"
                >
                  Import
                </Button>
              )}
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
}
