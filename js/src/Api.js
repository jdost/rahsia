import SwaggerClient from "swagger-client";

var apiClient;
var onLoad = new SwaggerClient({
  url: window.location.origin + "/openapi.json",
}).then(function (client) {
  apiClient = client;
});

export function getSecrets(triggerUpdateFunc) {
  return onLoad.then(function () {
    return apiClient.apis.secrets
      .listSecrets({ all: true })
      .then(function (reqs) {
        return reqs.obj.map(function (secret) {
          secret.update = function updateSecret(secrets) {
            const body = {
              name: secret.name,
              namespace: secret.namespace,
              secrets: secrets,
            };
            return setSecret(body).then(function () {
              triggerUpdateFunc();
              return;
            });
          };

          return secret;
        });
      });
  });
}

export function setSecret(secret) {
  return onLoad.then(function () {
    return apiClient.apis.secrets
      .setSecret({}, { requestBody: secret })
      .then(function (reqs) {
        return reqs.obj;
      });
  });
}
