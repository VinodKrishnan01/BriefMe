from marshmallow import Schema, fields, validate, ValidationError

class ActionSchema(Schema):
    """Schema for action items."""
    text = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    owner = fields.Str(allow_none=True, validate=validate.Length(max=100))
    due_date = fields.Date(allow_none=True, format='%Y-%m-%d')

class CreateBriefSchema(Schema):
    """Schema for creating a new brief."""
    source_text = fields.Str(
        required=True, 
        validate=validate.Length(min=1, max=10000),
        error_messages={'required': 'Source text is required'}
    )
    client_session_id = fields.Str(
        required=True,
        validate=validate.Length(equal=36),
        error_messages={'required': 'Client session ID is required'}
    )

class BriefResponseSchema(Schema):
    """Schema for brief response."""
    id = fields.Str(required=True)
    client_session_id = fields.Str(required=True)
    source_text = fields.Str(required=True)
    summary = fields.Str(required=True)
    decisions = fields.List(fields.Str(), missing=[])
    actions = fields.List(fields.Nested(ActionSchema), missing=[])
    questions = fields.List(fields.Str(), missing=[])
    created_at = fields.DateTime(required=True)
    sha256 = fields.Str(required=True)

class BriefSummarySchema(Schema):
    """Schema for brief summary in list view."""
    id = fields.Str(required=True)
    summary = fields.Str(required=True)
    created_at = fields.DateTime(required=True)
    source_text_preview = fields.Str(required=True)

class ErrorSchema(Schema):
    """Schema for error responses."""
    error = fields.Str(required=True)
    message = fields.Str(required=True)
    code = fields.Int(missing=400)