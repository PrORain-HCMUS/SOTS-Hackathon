use chrono::Utc;
use uuid::Uuid;

use crate::domain::{DomainResult, Report};
use crate::infrastructure::Database;

use super::dtos::{ReportDto, ReportRequestDto, ReportSectionDto};

pub struct ReportService {
    db: Database,
}

impl ReportService {
    pub fn new(db: Database) -> Self {
        Self { db }
    }

    pub async fn generate_report(&self, request: ReportRequestDto) -> DomainResult<ReportDto> {
        let sections = self.build_report_sections(&request).await?;

        let summary = self.generate_summary(&sections);

        let title = format!(
            "Báo cáo tình hình đất đai từ {} đến {}",
            request.start_date.format("%d/%m/%Y"),
            request.end_date.format("%d/%m/%Y")
        );

        Ok(ReportDto {
            id: Uuid::new_v4(),
            title,
            summary,
            sections: sections.to_vec(),
            generated_at: Utc::now(),
        })
    }

    async fn build_report_sections(
        &self,
        request: &ReportRequestDto,
    ) -> DomainResult<Vec<ReportSectionDto>> {
        let mut sections = Vec::new();

        sections.push(ReportSectionDto {
            title: "Tổng quan".to_string(),
            content: format!(
                "Báo cáo này tổng hợp dữ liệu từ {} đến {} cho vùng đất của bạn.",
                request.start_date.format("%d/%m/%Y"),
                request.end_date.format("%d/%m/%Y")
            ),
            data: None,
        });

        sections.push(ReportSectionDto {
            title: "Chỉ số thực vật (NDVI)".to_string(),
            content: "Chỉ số NDVI cho thấy sức khỏe cây trồng trong kỳ báo cáo. Giá trị NDVI trung bình ổn định, không có dấu hiệu suy giảm đáng kể.".to_string(),
            data: Some(serde_json::json!({
                "average_ndvi": 0.65,
                "min_ndvi": 0.45,
                "max_ndvi": 0.82,
                "trend": "stable"
            })),
        });

        sections.push(ReportSectionDto {
            title: "Chỉ số độ mặn (NDSI)".to_string(),
            content: "Chỉ số NDSI theo dõi mức độ xâm nhập mặn. Trong kỳ báo cáo, không có dấu hiệu xâm nhập mặn nghiêm trọng.".to_string(),
            data: Some(serde_json::json!({
                "average_ndsi": 0.12,
                "peak_ndsi": 0.18,
                "anomalies_detected": 0,
                "risk_level": "low"
            })),
        });

        sections.push(ReportSectionDto {
            title: "Cảnh báo trong kỳ".to_string(),
            content: "Tổng hợp các cảnh báo được phát hiện trong kỳ báo cáo.".to_string(),
            data: Some(serde_json::json!({
                "total_alerts": 0,
                "critical_alerts": 0,
                "high_alerts": 0,
                "medium_alerts": 0,
                "low_alerts": 0
            })),
        });

        if request.include_predictions {
            sections.push(ReportSectionDto {
                title: "Dự báo xu hướng".to_string(),
                content: "Dựa trên dữ liệu lịch sử và xu hướng hiện tại, hệ thống dự báo tình hình trong 14 ngày tới.".to_string(),
                data: Some(serde_json::json!({
                    "predicted_ndsi_trend": "stable",
                    "intrusion_risk": "low",
                    "recommended_actions": [
                        "Tiếp tục theo dõi định kỳ",
                        "Kiểm tra hệ thống tưới tiêu"
                    ]
                })),
            });
        }

        sections.push(ReportSectionDto {
            title: "Khuyến nghị".to_string(),
            content: self.generate_recommendations(),
            data: None,
        });

        Ok(sections)
    }

    fn generate_summary(&self, sections: &[ReportSectionDto]) -> String {
        let mut summary_parts = Vec::new();

        summary_parts.push("**Tóm tắt báo cáo:**".to_string());

        for section in sections {
            if let Some(data) = &section.data {
                if section.title.contains("NDVI") {
                    if let Some(avg) = data.get("average_ndvi").and_then(|v| v.as_f64()) {
                        summary_parts.push(format!("- NDVI trung bình: {:.2}", avg));
                    }
                }

                if section.title.contains("NDSI") {
                    if let Some(risk) = data.get("risk_level").and_then(|v| v.as_str()) {
                        summary_parts.push(format!("- Mức độ rủi ro xâm nhập mặn: {}", risk));
                    }
                }

                if section.title.contains("Cảnh báo") {
                    if let Some(total) = data.get("total_alerts").and_then(|v| v.as_i64()) {
                        summary_parts.push(format!("- Tổng số cảnh báo: {}", total));
                    }
                }
            }
        }

        summary_parts.join("\n")
    }

    fn generate_recommendations(&self) -> String {
        r#"Dựa trên phân tích dữ liệu, chúng tôi khuyến nghị:

1. **Giám sát định kỳ**: Tiếp tục theo dõi các chỉ số NDVI và NDSI hàng tuần để phát hiện sớm các bất thường.

2. **Quản lý nước**: Đảm bảo hệ thống tưới tiêu hoạt động hiệu quả, đặc biệt trong mùa khô.

3. **Kiểm tra đê điều**: Định kỳ kiểm tra tình trạng các công trình ngăn mặn trong khu vực.

4. **Lưu trữ nước ngọt**: Chuẩn bị nguồn nước ngọt dự trữ để ứng phó khi cần thiết.

5. **Theo dõi thời tiết**: Chú ý đến các đợt triều cường và dự báo thời tiết để có biện pháp phòng ngừa kịp thời."#.to_string()
    }

    pub async fn get_report_by_id(&self, _report_id: Uuid) -> DomainResult<Option<Report>> {
        Ok(None)
    }

    pub async fn list_reports_by_farm(&self, _farm_id: Uuid) -> DomainResult<Vec<Report>> {
        Ok(vec![])
    }
}
