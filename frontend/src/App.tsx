import { Flex } from "@chakra-ui/react";
import "./index.css";
import RuleHeaderList from "./components/RuleHeaderList";
import RuleDetail from "./components/RuleDetail";

function App() {
  return (
    <Flex h="100vh" w="100vw" overflow="hidden">
      <RuleHeaderList />
      <RuleDetail />
    </Flex>
  );
}

export default App;
