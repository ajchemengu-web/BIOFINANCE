import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../errors/app_exception.dart';

/// Thin HTTP wrapper around the BioFinance API. Attaches the merchant
/// bearer token (set by MerchantAuthService after sign-in) to every
/// request — now needed since POST /payments/request and
/// POST /payments/{id}/cancel require real merchant authentication
/// (docs/roadmap.md Phase 5, "Real merchant authentication"). Mirrors
/// mobile/'s ApiClient exactly.
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? _accessToken;

  void setAccessToken(String? token) => _accessToken = token;

  Uri _uri(String path) => Uri.parse('$apiBaseUrl$path');

  Map<String, String> _headers({Map<String, String>? extra}) => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
        ...?extra,
      };

  dynamic _decode(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = response.body;
      try {
        final body = jsonDecode(response.body);
        if (body is Map && body['detail'] != null) message = body['detail'].toString();
      } catch (_) {
        // Body wasn't JSON — fall back to the raw text set above.
      }
      throw ApiException(response.statusCode, message);
    }
    if (response.body.isEmpty) return null;
    return jsonDecode(response.body);
  }

  Future<dynamic> get(String path) async {
    final response = await _client.get(_uri(path), headers: _headers());
    return _decode(response);
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body, Map<String, String>? headers}) async {
    final response = await _client.post(
      _uri(path),
      headers: _headers(extra: headers),
      body: body == null ? null : jsonEncode(body),
    );
    return _decode(response);
  }
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
