import { Button, Em, Heading, Input } from "@chakra-ui/react";
import { Field } from "./components/ui/field";
import { toaster } from "./components/ui/toaster";

export function SecretForm({ target, reset }) {
  if (target.name.length === 0) {
    return <form />;
  }

  const fields = target.secrets.map(function (secret) {
    const fillerValue = new Array(secret.length + 1).join("*");
    return (
      <Field
        key={secret.name}
        label={secret.name}
        helperText={secret.note}
        pb="4"
      >
        <Input name={secret.name} placeholder={fillerValue} />
      </Field>
    );
  });

  function submitChanges(e) {
    e.preventDefault();
    const secrets = [];
    new FormData(e.target).forEach(function (v, k) {
      secrets.push({
        name: k,
        value: v,
      });
    });
    target
      .update(secrets)
      .then(function () {
        toaster.create({
          type: "success",
          description: `Updated secret ${target.name} in ${target.namespace}`,
        });
        reset();
      })
      .catch(function (err) {
        toaster.create({
          type: "error",
          description: `Failed to update secret ${target.name} in ${target.namespace}`,
        });
      });
  }

  return (
    <form onSubmit={submitChanges}>
      <Heading size="xl" mb="8">
        Editting {target.name} in <Em>{target.namespace}</Em>
      </Heading>
      {fields}
      <Button type="submit">Submit</Button>
    </form>
  );
}
