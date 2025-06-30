import pytest
from unittest.mock import patch, MagicMock
import os
import gspread # Added import for gspread

# Import the function to be tested
from reddit_fetch.api import export_to_google_sheet
from reddit_fetch.config import GOOGLE_SERVICE_ACCOUNT_KEY_PATH # Keep this for reference, but we'll patch it

# Sample data for testing
SAMPLE_POSTS = [
    {
        "title": "Test Post 1",
        "url": "http://example.com/post1",
        "subreddit": "testsubreddit",
        "author": "testuser1",
        "score": 100,
        "type": "post",
        "created_utc": 1678886400,
        "selftext": "This is the selftext for post 1.",
        "comments": [
            {"author": "commenter1", "body": "Great post!", "score": 5},
            {"author": "commenter2", "body": "Nice one.", "score": 2}
        ]
    },
    {
        "title": "Comment in: Another Post",
        "url": "http://example.com/comment1",
        "subreddit": "another_sub",
        "author": "testuser2",
        "score": 50,
        "type": "comment",
        "created_utc": 1678886500,
        "body": "This is a saved comment."
    }
]

@pytest.fixture
def mock_gspread():
    with patch('gspread.authorize') as mock_authorize:
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()

        mock_authorize.return_value = mock_gc
        mock_gc.open.return_value = mock_spreadsheet
        mock_gc.create.return_value = mock_spreadsheet # Ensure create also returns the mock spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_spreadsheet.add_worksheet.return_value = mock_worksheet
        # mock_spreadsheet.share.return_value = None # This line is not needed and can be removed

        yield mock_authorize, mock_gc, mock_spreadsheet, mock_worksheet

@pytest.fixture
def mock_service_account_credentials():
    with patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
        mock_creds.return_value = MagicMock(client_email="test-service-account@example.com")
        yield mock_creds

@pytest.fixture(autouse=True)
def patch_google_service_account_key_path():
    # Patch the GOOGLE_SERVICE_ACCOUNT_KEY_PATH in config and api modules
    with patch('reddit_fetch.config.GOOGLE_SERVICE_ACCOUNT_KEY_PATH', '/tmp/dummy_key.json'), \
         patch('reddit_fetch.api.GOOGLE_SERVICE_ACCOUNT_KEY_PATH', '/tmp/dummy_key.json'):
        yield

def test_export_to_google_sheet_success(mock_gspread, mock_service_account_credentials):
    mock_authorize, mock_gc, mock_spreadsheet, mock_worksheet = mock_gspread

    # Test successful export
    result = export_to_google_sheet(SAMPLE_POSTS, spreadsheet_name="TestSheet", worksheet_name="TestWorksheet")

    assert result is True
    mock_authorize.assert_called_once()
    mock_gc.open.assert_called_once_with("TestSheet")
    mock_spreadsheet.worksheet.assert_called_once_with("TestWorksheet")
    mock_worksheet.clear.assert_called_once()
    mock_worksheet.append_row.assert_called_once()
    mock_worksheet.append_rows.assert_called_once()

def test_export_to_google_sheet_no_key_path(mock_gspread, mock_service_account_credentials):
    # Patch GOOGLE_SERVICE_ACCOUNT_KEY_PATH to None for this test
    with patch('reddit_fetch.config.GOOGLE_SERVICE_ACCOUNT_KEY_PATH', None), \
         patch('reddit_fetch.api.GOOGLE_SERVICE_ACCOUNT_KEY_PATH', None):
        result = export_to_google_sheet(SAMPLE_POSTS)
        assert result is False

def test_export_to_google_sheet_spreadsheet_not_found(mock_gspread, mock_service_account_credentials):
    mock_authorize, mock_gc, mock_spreadsheet, mock_worksheet = mock_gspread
    mock_gc.open.side_effect = gspread.exceptions.SpreadsheetNotFound

    result = export_to_google_sheet(SAMPLE_POSTS, spreadsheet_name="NonExistentSheet")

    assert result is True  # Should create and succeed
    mock_gc.create.assert_called_once_with("NonExistentSheet")
    mock_spreadsheet.share.assert_called_once_with(mock_service_account_credentials.return_value.client_email, perm_type='user', role='writer')
    mock_spreadsheet.worksheet.assert_called_once_with("Saved Posts") # Default worksheet name

def test_export_to_google_sheet_worksheet_not_found(mock_gspread, mock_service_account_credentials):
    mock_authorize, mock_gc, mock_spreadsheet, mock_worksheet = mock_gspread
    mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound

    result = export_to_google_sheet(SAMPLE_POSTS, spreadsheet_name="TestSheet", worksheet_name="NonExistentWorksheet")

    assert result is True
    mock_spreadsheet.add_worksheet.assert_called_once_with(title="NonExistentWorksheet", rows="100", cols="20")
    mock_worksheet.clear.assert_called_once()
    mock_worksheet.append_row.assert_called_once()
    mock_worksheet.append_rows.assert_called_once()

def test_export_to_google_sheet_exception(mock_gspread, mock_service_account_credentials):
    mock_authorize, mock_gc, mock_spreadsheet, mock_worksheet = mock_gspread
    mock_authorize.side_effect = Exception("Authentication error")

    result = export_to_google_sheet(SAMPLE_POSTS)

    assert result is False
    mock_authorize.assert_called_once()
