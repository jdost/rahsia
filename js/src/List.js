import { Button, Em } from "@chakra-ui/react";
import { getSecrets } from "./Api.js";
import { useState, useEffect } from "react";
import {
  RiErrorWarningFill,
  RiQuestionFill,
  RiShieldKeyholeFill,
} from "react-icons/ri";

export function SecretsList({ formControl }) {
  const [secrets, setSecrets] = useState([]);
  const [trigger, setTrigger] = useState(0);

  function triggerUpdate() {
    setTrigger(trigger + 1);
  }

  useEffect(
    function () {
      getSecrets(triggerUpdate).then(setSecrets);
    },
    [trigger],
  );

  const renderedSecrets = secrets.map(function (secret) {
    function activate() {
      formControl(secret);
    }
    const missing = secret.secrets.filter((s) => s.length === 0);
    const key = `${secret.namespace}.${secret.name}`;
    var icon = <RiShieldKeyholeFill />;
    var palette = "cyan";

    if (missing.length === secret.secrets.length) {
      palette = "red";
      icon = <RiErrorWarningFill />;
    } else if (missing.length !== 0) {
      palette = "orange";
      icon = <RiQuestionFill />;
    }

    return (
      <li key={key}>
        <Button
          w="100%"
          colorPalette={palette}
          variant="ghost"
          onClick={activate}
        >
          {icon} {secret.name}{" "}
          <Em fontSize="xs" opacity="0.75">
            ({secret.namespace})
          </Em>
        </Button>
      </li>
    );
  });
  return <ul>{renderedSecrets}</ul>;
}
