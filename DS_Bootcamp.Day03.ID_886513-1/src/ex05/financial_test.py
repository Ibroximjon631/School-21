import pytest
import requests

from financial import get_args, get_response, parse_html


def test_get_args(monkeypatch):
    monkeypatch.setattr('sys.argv', ['financial.py', 'MSFT', 'Total Revenue'])
    ticker, field = get_args()
    assert ticker == 'MSFT'
    assert field == 'Total Revenue'


def test_get_response_valid():
    url = 'https://finance.yahoo.com/quote/MSFT/financials'
    response = get_response(url)
    assert response.status_code == 200


def test_get_response_invalid(mocker):
    mocker.patch('requests.get', side_effect=requests.exceptions.HTTPError("404 Client Error: Not Found for url"))

    with pytest.raises(Exception) as excinfo:
        get_response('https://finance.yahoo.com/quote/INVALID_TICKER/financials')

    assert 'URL does not exist' in str(excinfo.value)


def test_parse_html_valid(mocker):
    mock_response = mocker.Mock()
    mock_response.text = '<div class="row lv-0"><div class="rowTitle">Total Revenue</div><div class="column yf-">1000000</div></div>'

    result = parse_html(mock_response, 'Total Revenue')

    assert isinstance(result, tuple)
    assert result == ('1000000',)


def test_parse_html_invalid_field(mocker):
    mock_response = mocker.Mock()
    mock_response.text = '<div class="row lv-0"><div class="rowTitle">Total Revenue</div><div class="column yf-">1000000</div></div>'

    with pytest.raises(Exception) as excinfo:
        parse_html(mock_response, 'Invalid Field')

    assert 'The requested field does not exist' in str(excinfo.value)
