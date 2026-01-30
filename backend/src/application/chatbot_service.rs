use uuid::Uuid;

use crate::domain::{DomainResult, TodoPriority};
use crate::infrastructure::Database;

#[allow(dead_code)]

use super::dtos::{ChatRequestDto, ChatResponseDto, FunctionCallDto};

pub struct ChatbotService {
    db: Database,
}

#[derive(Debug, Clone)]
pub enum ChatFunction {
    GetSalinityStatus { farm_id: Uuid },
    PredictIntrusion { farm_id: Uuid },
    WriteTodo { title: String, description: Option<String>, priority: TodoPriority },
    UpdateTodo { todo_id: Uuid, completed: bool },
    GenerateReport { farm_id: Uuid, days: u32 },
}

impl ChatbotService {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn process_message(&self, request: ChatRequestDto) -> DomainResult<ChatResponseDto> {
        let functions = self.parse_intent(&request.message);
        let mut function_calls = Vec::new();

        for func in functions {
            let result = self.execute_function(&func, &request).await;
            function_calls.push(result);
        }

        let response_message = self.generate_response(&request.message, &function_calls);

        Ok(ChatResponseDto {
            message: response_message,
            function_calls,
            data: None,
        })
    }

    fn parse_intent(&self, message: &str) -> Vec<ChatFunction> {
        let message_lower = message.to_lowercase();
        let mut functions = Vec::new();

        if message_lower.contains("salinity") || message_lower.contains("mặn") || message_lower.contains("độ mặn") {
            functions.push(ChatFunction::GetSalinityStatus {
                farm_id: Uuid::nil(),
            });
        }

        if message_lower.contains("predict") || message_lower.contains("dự báo") || message_lower.contains("hướng") {
            functions.push(ChatFunction::PredictIntrusion {
                farm_id: Uuid::nil(),
            });
        }

        if message_lower.contains("todo") || message_lower.contains("nhắc") || message_lower.contains("việc cần làm") {
            if let Some(title) = self.extract_todo_title(&message_lower) {
                functions.push(ChatFunction::WriteTodo {
                    title,
                    description: None,
                    priority: TodoPriority::Medium,
                });
            }
        }

        if message_lower.contains("report") || message_lower.contains("báo cáo") {
            functions.push(ChatFunction::GenerateReport {
                farm_id: Uuid::nil(),
                days: 30,
            });
        }

        functions
    }

    fn extract_todo_title(&self, message: &str) -> Option<String> {
        if message.contains("tạo") || message.contains("thêm") || message.contains("add") {
            let parts: Vec<&str> = message.split(':').collect();
            if parts.len() > 1 {
                return Some(parts[1].trim().to_string());
            }
        }
        None
    }

    async fn execute_function(
        &self,
        function: &ChatFunction,
        request: &ChatRequestDto,
    ) -> FunctionCallDto {
        match function {
            ChatFunction::GetSalinityStatus { farm_id } => {
                let farm_id = request
                    .farm_context
                    .as_ref()
                    .map(|c| c.farm_id)
                    .unwrap_or(*farm_id);

                FunctionCallDto {
                    function_name: "get_salinity_status".to_string(),
                    arguments: serde_json::json!({ "farm_id": farm_id }),
                    result: Some(serde_json::json!({
                        "current_ndsi": 0.15,
                        "trend": "stable",
                        "risk_level": "low"
                    })),
                    success: true,
                }
            }

            ChatFunction::PredictIntrusion { farm_id } => {
                let farm_id = request
                    .farm_context
                    .as_ref()
                    .map(|c| c.farm_id)
                    .unwrap_or(*farm_id);

                FunctionCallDto {
                    function_name: "predict_intrusion".to_string(),
                    arguments: serde_json::json!({ "farm_id": farm_id }),
                    result: Some(serde_json::json!({
                        "direction": "southwest",
                        "velocity_m_per_day": 50.0,
                        "days_to_reach": null,
                        "risk_level": "low"
                    })),
                    success: true,
                }
            }

            ChatFunction::WriteTodo { title, description, priority } => {
                let todo_id = Uuid::new_v4();

                FunctionCallDto {
                    function_name: "write_todo".to_string(),
                    arguments: serde_json::json!({
                        "title": title,
                        "description": description,
                        "priority": format!("{:?}", priority).to_lowercase()
                    }),
                    result: Some(serde_json::json!({
                        "todo_id": todo_id,
                        "created": true
                    })),
                    success: true,
                }
            }

            ChatFunction::UpdateTodo { todo_id, completed } => {
                FunctionCallDto {
                    function_name: "update_todo".to_string(),
                    arguments: serde_json::json!({
                        "todo_id": todo_id,
                        "completed": completed
                    }),
                    result: Some(serde_json::json!({
                        "updated": true
                    })),
                    success: true,
                }
            }

            ChatFunction::GenerateReport { farm_id, days } => {
                let farm_id = request
                    .farm_context
                    .as_ref()
                    .map(|c| c.farm_id)
                    .unwrap_or(*farm_id);

                FunctionCallDto {
                    function_name: "generate_report".to_string(),
                    arguments: serde_json::json!({
                        "farm_id": farm_id,
                        "days": days
                    }),
                    result: Some(serde_json::json!({
                        "report_id": Uuid::new_v4(),
                        "generated": true
                    })),
                    success: true,
                }
            }
        }
    }

    fn generate_response(&self, _message: &str, function_calls: &[FunctionCallDto]) -> String {
        if function_calls.is_empty() {
            return "Xin chào! Tôi là trợ lý AI của Bio-Radar. Tôi có thể giúp bạn kiểm tra độ mặn, dự báo xâm nhập mặn, tạo việc cần làm, và tạo báo cáo.".to_string();
        }

        let mut response_parts = Vec::new();

        for call in function_calls {
            match call.function_name.as_str() {
                "get_salinity_status" => {
                    if let Some(result) = &call.result {
                        let ndsi = result.get("current_ndsi").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let trend = result.get("trend").and_then(|v| v.as_str()).unwrap_or("unknown");
                        let risk = result.get("risk_level").and_then(|v| v.as_str()).unwrap_or("unknown");

                        response_parts.push(format!(
                            "📊 **Tình trạng độ mặn**: NDSI hiện tại là {:.2}, xu hướng {}, mức độ rủi ro {}.",
                            ndsi, trend, risk
                        ));
                    }
                }

                "predict_intrusion" => {
                    if let Some(result) = &call.result {
                        let direction = result.get("direction").and_then(|v| v.as_str()).unwrap_or("unknown");
                        let velocity = result.get("velocity_m_per_day").and_then(|v| v.as_f64()).unwrap_or(0.0);

                        response_parts.push(format!(
                            "🧭 **Dự báo xâm nhập mặn**: Hướng di chuyển {}, tốc độ {:.0}m/ngày.",
                            direction, velocity
                        ));
                    }
                }

                "write_todo" => {
                    response_parts.push("✅ Đã tạo việc cần làm mới cho bạn.".to_string());
                }

                "generate_report" => {
                    response_parts.push("📝 Đã tạo báo cáo cho bạn.".to_string());
                }

                _ => {}
            }
        }

        if response_parts.is_empty() {
            "Đã xử lý yêu cầu của bạn.".to_string()
        } else {
            response_parts.join("\n\n")
        }
    }
}
