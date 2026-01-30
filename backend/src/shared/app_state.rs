use sqlx::PgPool;
use std::sync::Arc;
use crate::modules::monitoring::ai::engine::AiEngine;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub ai_engine: Option<Arc<AiEngine>>,
}

impl AppState {
    pub fn new(db: PgPool) -> Self {
        Self { db, ai_engine: None }
    }

    pub fn with_ai_engine(mut self, engine: AiEngine) -> Self {
        self.ai_engine = Some(Arc::new(engine));
        self
    }
}