# import asyncio
# import json

# from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

# from src.controllers.telegram_realtime_controller import TelegramRealtimeController
# from src.logs.logs import logger
# from src.routers.auth_router import get_current_org

# # Protected routes
# router = APIRouter()
# controller = TelegramRealtimeController()


# @router.websocket("/ws/realtime")
# async def websocket_realtime(
#     websocket: WebSocket,
#     group_id: int = Query(...),
#     token: str = Query(...),
# ):
#     """WebSocket endpoint for real-time message monitoring"""
#     await websocket.accept()

#     current_org = await get_current_org(token)

#     if not current_org:
#         await websocket.send_text(json.dumps({"error": "Invalid token"}))
#         await websocket.close()
#         return

#     try:
#         # Setup handler using controller
#         handler = await controller.setup_realtime_handler(group_id, current_org)
#         handler_data = await controller.create_websocket_handler(handler, group_id)

#         message_queue = handler_data["message_queue"]
#         websocket_connected = handler_data["websocket_connected"]
#         listen_task = handler_data["listen_task"]
#         process_task = handler_data["process_task"]

#         try:
#             logger.info("WebSocket loop started, waiting for messages...")
#             while websocket_connected:
#                 try:
#                     message_data = await message_queue.get()
#                     if websocket_connected:
#                         await websocket.send_text(json.dumps(message_data, default=str))
#                 except WebSocketDisconnect:
#                     logger.info("WebSocket disconnected, stopping background tasks...")
#                     websocket_connected = False
#                     break
#                 except Exception as e:
#                     logger.error(f"Error in WebSocket loop: {e}")
#                     websocket_connected = False
#                     break

#         except Exception as e:
#             logger.error(f"Unexpected error in WebSocket handler: {e}")
#         finally:
#             await controller.cleanup_handler(handler, listen_task, process_task)

#     except Exception as e:
#         logger.error(f"Error setting up realtime handler: {e}")
#         await websocket.close()


# @router.websocket("/ws/intelligent-response")
# async def websocket_realtime_intelligent_response(
#     websocket: WebSocket,
#     token: str = Query(...),
# ):
#     """WebSocket endpoint for intelligent response monitoring"""
#     await websocket.accept()

#     current_org = await get_current_org(token)

#     if not current_org:
#         await websocket.send_text(json.dumps({"error": "Invalid token"}))
#         await websocket.close()
#         return

#     try:
#         # Setup handler using controller
#         handler = await controller.setup_intelligent_response_handler(current_org)
#         handler_data = await controller.create_websocket_handler(handler)

#         message_queue = handler_data["message_queue"]
#         websocket_connected = handler_data["websocket_connected"]
#         listen_task = handler_data["listen_task"]
#         process_task = handler_data["process_task"]

#         try:
#             logger.info("WebSocket loop started, waiting for messages...")
#             while websocket_connected:
#                 try:
#                     message_data = await message_queue.get()
#                     if websocket_connected:
#                         await websocket.send_text(json.dumps(message_data, default=str))
#                 except WebSocketDisconnect:
#                     logger.info("WebSocket disconnected, stopping background tasks...")
#                     websocket_connected = False
#                     break
#                 except Exception as e:
#                     logger.error(f"Error in WebSocket loop: {e}")
#                     websocket_connected = False
#                     break

#         except Exception as e:
#             logger.error(f"Unexpected error in WebSocket handler: {e}")
#         finally:
#             await controller.cleanup_handler(handler, listen_task, process_task)

#     except Exception as e:
#         logger.error(f"Error setting up intelligent response handler: {e}")
#         await websocket.close()
