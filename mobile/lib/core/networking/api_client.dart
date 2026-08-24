import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';

/// Thin HTTP wrapper around the BioFinance API. Request/response handling
/// (auth headers, error mapping) is filled in as features land in Phase 1-2.
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$apiBaseUrl$path');

  Future<http.Response> get(String path) => _client.get(_uri(path));
}
