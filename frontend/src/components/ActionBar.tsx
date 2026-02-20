import { useState } from "react";
import { Button, Flex } from "@chakra-ui/react";
import {
  LuCopy,
  LuDownload,
  LuTrash2,
  LuSend,
  LuCheck,
  LuX,
  LuArchive,
  LuUpload,
} from "react-icons/lu";
import type { RuleHeader } from "../types";
import { useRulesStore } from "../store/rulesStore";
import CloneConfirmDialog from "./CloneConfirmDialog";
import ImportDialog from "./ImportDialog";

interface ActionBarProps {
  header: RuleHeader;
}

export default function ActionBar({ header }: ActionBarProps) {
  const { updateStatus, deleteHeader, exportCSV, selectHeader } =
    useRulesStore();
  const [showClone, setShowClone] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [confirming, setConfirming] = useState<string | null>(null);

  const handleStatusChange = async (newStatus: string) => {
    try {
      await updateStatus(header.id, newStatus);
      setConfirming(null);
    } catch {
      setConfirming(null);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteHeader(header.id);
      setConfirming(null);
    } catch {
      setConfirming(null);
    }
  };

  const renderConfirmation = (
    action: string,
    label: string,
    onConfirm: () => void,
    colorScheme = "red"
  ) => {
    if (confirming === action) {
      return (
        <Flex gap={1} align="center">
          <Button
            size="sm"
            colorPalette={colorScheme}
            onClick={onConfirm}
            fontWeight="600"
          >
            <LuCheck />
            Confirm {label}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setConfirming(null)}
          >
            <LuX />
          </Button>
        </Flex>
      );
    }
    return null;
  };

  return (
    <>
      <Flex
        gap={2}
        wrap="wrap"
        p={4}
        bg="white"
        borderRadius="lg"
        borderWidth="1px"
        borderColor="gray.200"
        mb={4}
        align="center"
      >
        {/* --- Draft actions --- */}
        {header.status === "draft" && (
          <>
            {confirming === "submit" ? (
              renderConfirmation("submit", "Submit", () =>
                handleStatusChange("in_review")
              , "orange")
            ) : (
              <Button
                size="sm"
                bg="#FFC72C"
                color="#1A1A1A"
                fontWeight="600"
                _hover={{ bg: "#E6B327" }}
                onClick={() => setConfirming("submit")}
              >
                <LuSend />
                Submit for Review
              </Button>
            )}

            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowClone(true)}
            >
              <LuCopy />
              Clone
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => exportCSV(header.id)}
            >
              <LuDownload />
              Export CSV
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowImport(true)}
            >
              <LuUpload />
              Import CSV
            </Button>

            {confirming === "delete" ? (
              renderConfirmation("delete", "Delete", handleDelete)
            ) : (
              <Button
                size="sm"
                variant="outline"
                colorPalette="red"
                onClick={() => setConfirming("delete")}
              >
                <LuTrash2 />
                Delete
              </Button>
            )}
          </>
        )}

        {/* --- In Review actions --- */}
        {header.status === "in_review" && (
          <>
            {confirming === "approve" ? (
              renderConfirmation("approve", "Approve", () =>
                handleStatusChange("approved")
              , "green")
            ) : (
              <Button
                size="sm"
                colorPalette="green"
                fontWeight="600"
                onClick={() => setConfirming("approve")}
              >
                <LuCheck />
                Approve
              </Button>
            )}

            {confirming === "reject" ? (
              renderConfirmation("reject", "Reject", () =>
                handleStatusChange("draft")
              , "red")
            ) : (
              <Button
                size="sm"
                variant="outline"
                colorPalette="red"
                onClick={() => setConfirming("reject")}
              >
                <LuX />
                Reject
              </Button>
            )}

            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowClone(true)}
            >
              <LuCopy />
              Clone
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => exportCSV(header.id)}
            >
              <LuDownload />
              Export CSV
            </Button>
          </>
        )}

        {/* --- Approved actions --- */}
        {header.status === "approved" && (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowClone(true)}
            >
              <LuCopy />
              Clone
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => exportCSV(header.id)}
            >
              <LuDownload />
              Export CSV
            </Button>

            {confirming === "archive" ? (
              renderConfirmation("archive", "Archive", () =>
                handleStatusChange("archived")
              , "blue")
            ) : (
              <Button
                size="sm"
                variant="outline"
                colorPalette="blue"
                onClick={() => setConfirming("archive")}
              >
                <LuArchive />
                Archive
              </Button>
            )}
          </>
        )}

        {/* --- Archived actions --- */}
        {header.status === "archived" && (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowClone(true)}
            >
              <LuCopy />
              Clone
            </Button>

            <Button
              size="sm"
              variant="outline"
              onClick={() => exportCSV(header.id)}
            >
              <LuDownload />
              Export CSV
            </Button>
          </>
        )}
      </Flex>

      {/* Dialogs */}
      <CloneConfirmDialog
        open={showClone}
        header={header}
        onClose={() => setShowClone(false)}
        onCloned={(newHeader) => {
          setShowClone(false);
          selectHeader(newHeader.id);
        }}
      />
      <ImportDialog
        open={showImport}
        headerId={header.id}
        onClose={() => setShowImport(false)}
      />
    </>
  );
}
