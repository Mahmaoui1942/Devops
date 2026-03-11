import { Client } from '@stomp/stompjs';
import SockJS from 'sockjs-client';

const _APIURL = "https://pixel-api.edgarbaudry.dev"; //"https://pixel-war-api.herokuapp.com" "http://localhost:8090"
const connecEndPoint = "/connect";
const requestGetEndPoint = "/grid/get";
const requestPlaceEndPoint = "/app/grid/place";
const subscribePixelUpdateEndPoint = "/topic/pixel_update";
const subscribeFullUpdateEndPoint = "/topic/full_update";
const connectionAttemptsDelay = 500;//ms
var isConnected = false;

var stompClient = null;

var fullUpdateCallBack = () => {};
var pixelUpdateCallBack = () => {};
var errorCallBack = () => {};
var connectCallBack = () => {};


export const connect = (fullUpdateCallBackFunc, pixelUpdateCallBackFunc, connectCallBackFunc, errorCallBackFunc) => {
  fullUpdateCallBack = fullUpdateCallBackFunc;
  pixelUpdateCallBack = pixelUpdateCallBackFunc;
  errorCallBack = errorCallBackFunc;
  connectCallBack = connectCallBackFunc;

  // create STOMP client that uses SockJS
  const client = new Client({
    brokerURL: undefined, // we use webSocketFactory instead
    webSocketFactory: () => new SockJS(_APIURL + connecEndPoint),
    connectHeaders: {},
    debug: () => {}, // silence verbose logging (restore for debugging)
    reconnectDelay: connectionAttemptsDelay,
    onConnect: () => {
      isConnected = true;

      client.subscribe(subscribeFullUpdateEndPoint, (message) => {
        try {
          onFullUpdateReceived(JSON.parse(message.body));
        } catch (e) {
          console.error("Failed to parse full update payload", e);
        }
      });

      client.subscribe(subscribePixelUpdateEndPoint, (message) => {
        try {
          onPixelUpdateReceived(JSON.parse(message.body));
        } catch (e) {
          console.error("Failed to parse pixel update payload", e);
        }
      });

      connectCallBack();
    },
    onStompError: (frame) => {
      onError(frame);
    },
    onWebSocketClose: () => {
      isConnected = false;
    }
  });
  stompClient = client;
  client.activate();

  // return cleanup function
  return () => client.deactivate();
}

export const gridGet = () => {
  fetch(_APIURL + requestGetEndPoint)
  .then(async response => {
    const data = await response.json();

    // check for error response
    if (!response.ok) {
      // get error message from body or default to response statusText
      const error = (data && data.message) || response.statusText;
      onError(error);
      return;
    }

    onFullUpdateReceived(data);
  })
  .catch(error => {
    onError(error);
  });
}

export const gridPlace = (x, y, color) => {
  var message = {
    x:x,
    y:y,
    color:color
  };
  stompClient.publish({ destination: requestPlaceEndPoint, body: JSON.stringify(message) });
  pixelUpdateCallBack(message);
}

const reattemptConnection = () => {
  if(!isConnected){
    stompClient.connect({}, onConnected, onError);
  }
}

const onConnected = () => {
  console.log("Connection Success");

  isConnected = true;

  stompClient.subscribe(subscribeFullUpdateEndPoint, (payload) => {
    onFullUpdateReceived(JSON.parse(payload.body));
  });

  stompClient.subscribe(subscribePixelUpdateEndPoint, (payload) => {
    onPixelUpdateReceived(JSON.parse(payload.body));
  });

  connectCallBack();
}

// const convertRecievedMessageToJSON = (payload) => {
//   onMessageReceived(JSON.parse(payload.body));
// }

const onPixelUpdateReceived = (data)=>{
  // console.log("Pixel Update Arrived");
  // console.log(data);

  pixelUpdateCallBack(data);
}

const onFullUpdateReceived = (data)=>{
  // console.log("Message Arrived");
  // console.log(data);

  fullUpdateCallBack(data);
}

const onError = (err) => {
  console.error("beep boop error :(", err);
  isConnected = false;
  errorCallBack(err);
}