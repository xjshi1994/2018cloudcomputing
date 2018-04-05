//Code as below:

 

var getParameterByName = function(name, url) {

    if (!url) url = window.location.href;

   name = name.replace(/[\[\]]/g, "\\$&");

    console.log(name);

    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),

        results = regex.exec(url);

        console.log(results);

    if (!results) return null;

    if (!results[2]) return '';

    console.log(results[2]);

    return decodeURIComponent(results[2].replace(/\+/g, " "));

};

 

/*

    This method exchanges the Authorization Code received from Cognito upon a successful login,

    with temporary accessKey and secretKey IAM credentials.

 

    Resources:

    - https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html

    - https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-app-idp-settings.html

    - https://docs.aws.amazon.com/cognito/latest/developerguide/using-amazon-cognito-user-identity-pools-javascript-examples.html

*/

 

// Exchange code for id_token and credentials.

var exchangeAuthCodeForCredentials = function({

    auth_code, client_id, identity_pool_id, aws_region, user_pool_id, cognito_domain_url, redirect_uri

}) {

    return new Promise((resolve, reject) => {

        var settings = {

            url: `${cognito_domain_url}/oauth2/token`,

            method: 'POST',

            headers: {

                'Content-Type': 'application/x-www-form-urlencoded'

            },

            data: {

                grant_type: 'authorization_code',

                client_id: client_id,

                redirect_uri: redirect_uri,

                code: auth_code

            }

        };

 

        $.ajax(settings).done(function (response) {

            console.log('oauth2 token call responded');

 

            if (response.id_token) {

                // Add the User's Id Token to the Cognito credentials login map.

                AWS.config.credentials = new AWS.CognitoIdentityCredentials({

                    IdentityPoolId : identity_pool_id,

                    Logins : {

                        [`cognito-idp.${aws_region}.amazonaws.com/${user_pool_id}`]: response.id_token

                    }

                });

 

                AWS.config.credentials.refresh((error) => {

                    if (error) {

                        reject(error);

                    } else {

                        console.log('successfully logged in');

                        resolve(AWS.config.credentials);

                    }

                });

            } else {

                reject(response);

            }

        });

    });

};

