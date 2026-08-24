import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../errors/app_exception.dart';

/// Thin HTTP wrapper around the BioFinance API. Every endpoint BioPOS calls
/// today (POST /merchants, POST /payments/request, GET /payments/{id}) is
/// unauthenticated — there's no merchant-auth endpoint yet
/// (docs/roadmap.md Phase 5) — so unlike mobile/'s ApiClient this carries
/// no bearer token.
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$apiBaseUrl$path');

  Map<String, String> _headers({Map<String, String>? extra}) => {
        'Content-Type': 'application/json',
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
