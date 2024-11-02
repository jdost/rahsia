import "./App.css";
import { Provider } from "./components/ui/provider";
import { Box, Flex, Heading, Icon, Stack, Theme } from "@chakra-ui/react";
import { Toaster } from "./components/ui/toaster";
import { useState } from "react";
import { SecretForm } from "./Forms.js";
import { SecretsList } from "./List.js";
import { FaVault } from "react-icons/fa6";

function Header() {
  return (
    <Flex align="center" justify="flex-end" gap="4">
      <Icon fontSize="2xl">
        <FaVault />
      </Icon>
      <Heading size="2xl" textAlign="right">
        Rahsia
      </Heading>
    </Flex>
  );
}

function App() {
  const emptySecret = {
    name: "",
    namespace: "",
    secrets: [],
  };
  const [activeSecret, setFocus] = useState(emptySecret);

  function resetActiveSecret() {
    setFocus(emptySecret);
  }

  return (
    <Provider>
      <Box bg="cyan.950" p="4" w="100%">
        <Header />
      </Box>
      <Stack direction="row" h="100%">
        <Box w="sm" p="5" bg="cyan.950">
          <SecretsList formControl={setFocus} />
        </Box>
        <Box bg="white" w="100%" h="100%" p="20">
          <Theme appearance="light">
            <SecretForm target={activeSecret} reset={resetActiveSecret} />
          </Theme>
        </Box>
      </Stack>
      <Toaster />
    </Provider>
  );
}

export default App;
