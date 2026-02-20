import { useState } from "react";
import {
  Box,
  Button,
  CloseButton,
  Dialog,
  Flex,
  Input,
  Portal,
  Text,
} from "@chakra-ui/react";
import { useRulesStore } from "../store/rulesStore";

interface NewRuleDialogProps {
  open: boolean;
  onClose: () => void;
}

const INITIAL_FORM = {
  start_date: "",
  end_date: "",
  cost_category: "",
  rate_category: "",
  category: "",
  account_group: "",
  groupby_costcenter: false,
  groupby_account: false,
  fixed_variable_pct_split: "",
  fixed_variable_type: "",
};

export default function NewRuleDialog({ open, onClose }: NewRuleDialogProps) {
  const { createHeader, selectHeader } = useRulesStore();
  const [form, setForm] = useState(INITIAL_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleClose = () => {
    setForm(INITIAL_FORM);
    setError("");
    onClose();
  };

  const handleSubmit = async () => {
    setError("");

    if (!form.start_date || !form.end_date || !form.cost_category) {
      setError("Start date, end date, and cost category are required.");
      return;
    }

    setSaving(true);
    try {
      const data: Record<string, unknown> = {
        start_date: form.start_date,
        end_date: form.end_date,
        cost_category: form.cost_category,
        rate_category: form.rate_category || null,
        category: form.category || null,
        account_group: form.account_group || null,
        groupby_costcenter: form.groupby_costcenter,
        groupby_account: form.groupby_account,
        fixed_variable_pct_split: form.fixed_variable_pct_split
          ? parseFloat(form.fixed_variable_pct_split)
          : null,
        fixed_variable_type: form.fixed_variable_type || null,
      };

      const newHeader = await createHeader(data);
      await selectHeader(newHeader.id);
      handleClose();
    } catch {
      setError("Failed to create rule. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const updateField = (field: string, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(e) => {
        if (!e.open) handleClose();
      }}
      placement="center"
      size="lg"
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title fontWeight="700" color="#1A1A1A">
                New Rule
              </Dialog.Title>
            </Dialog.Header>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" />
            </Dialog.CloseTrigger>
            <Dialog.Body>
              {error && (
                <Box
                  bg="red.50"
                  color="red.600"
                  p={3}
                  borderRadius="md"
                  mb={4}
                  fontSize="sm"
                >
                  {error}
                </Box>
              )}

              <Box
                display="grid"
                gridTemplateColumns="repeat(2, 1fr)"
                gap={4}
              >
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Start Date *
                  </Text>
                  <Input
                    type="date"
                    size="sm"
                    value={form.start_date}
                    onChange={(e) => updateField("start_date", e.target.value)}
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    End Date *
                  </Text>
                  <Input
                    type="date"
                    size="sm"
                    value={form.end_date}
                    onChange={(e) => updateField("end_date", e.target.value)}
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Cost Category *
                  </Text>
                  <Input
                    size="sm"
                    placeholder="e.g. Fuel, Crew, Maintenance"
                    value={form.cost_category}
                    onChange={(e) =>
                      updateField("cost_category", e.target.value)
                    }
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Rate Category
                  </Text>
                  <Input
                    size="sm"
                    placeholder="e.g. Domestic, International"
                    value={form.rate_category}
                    onChange={(e) =>
                      updateField("rate_category", e.target.value)
                    }
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Category
                  </Text>
                  <Input
                    size="sm"
                    placeholder="e.g. Operating"
                    value={form.category}
                    onChange={(e) => updateField("category", e.target.value)}
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Account Group
                  </Text>
                  <Input
                    size="sm"
                    placeholder="e.g. Fuel-DOM"
                    value={form.account_group}
                    onChange={(e) =>
                      updateField("account_group", e.target.value)
                    }
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Fixed/Variable % Split
                  </Text>
                  <Input
                    size="sm"
                    type="number"
                    step="0.01"
                    placeholder="0.00 - 1.00"
                    value={form.fixed_variable_pct_split}
                    onChange={(e) =>
                      updateField("fixed_variable_pct_split", e.target.value)
                    }
                  />
                </Box>
                <Box>
                  <Text fontSize="xs" fontWeight="600" color="gray.600" mb={1}>
                    Fixed/Variable Type
                  </Text>
                  <select
                    value={form.fixed_variable_type}
                    onChange={(e) =>
                      updateField("fixed_variable_type", e.target.value)
                    }
                    style={{
                      padding: "6px 10px",
                      borderRadius: "6px",
                      border: "1px solid #e2e8f0",
                      fontSize: "13px",
                      width: "100%",
                      backgroundColor: "white",
                    }}
                  >
                    <option value="">Select...</option>
                    <option value="fixed">Fixed</option>
                    <option value="variable">Variable</option>
                    <option value="mixed">Mixed</option>
                  </select>
                </Box>
                <Box>
                  <Flex align="center" gap={2} mt={4}>
                    <input
                      type="checkbox"
                      checked={form.groupby_costcenter}
                      onChange={(e) =>
                        updateField("groupby_costcenter", e.target.checked)
                      }
                      id="groupby_costcenter"
                    />
                    <label
                      htmlFor="groupby_costcenter"
                      style={{ fontSize: "13px", color: "#333" }}
                    >
                      Group by Cost Center
                    </label>
                  </Flex>
                </Box>
                <Box>
                  <Flex align="center" gap={2} mt={4}>
                    <input
                      type="checkbox"
                      checked={form.groupby_account}
                      onChange={(e) =>
                        updateField("groupby_account", e.target.checked)
                      }
                      id="groupby_account"
                    />
                    <label
                      htmlFor="groupby_account"
                      style={{ fontSize: "13px", color: "#333" }}
                    >
                      Group by Account
                    </label>
                  </Flex>
                </Box>
              </Box>
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" onClick={handleClose} size="sm">
                Cancel
              </Button>
              <Button
                bg="#FFC72C"
                color="#1A1A1A"
                fontWeight="700"
                _hover={{ bg: "#E6B327" }}
                onClick={handleSubmit}
                loading={saving}
                size="sm"
              >
                Create Rule
              </Button>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
}
