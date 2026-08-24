import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/routing_policy.dart';

class RoutingRepository {
  RoutingRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<RoutingPolicy> fetch() async {
    final json = await _apiClient.get('/routing-policy') as Map<String, dynamic>;
    return RoutingPolicy.fromJson(json);
  }

  Future<RoutingPolicy> update(RoutingPolicy policy) async {
    final json = await _apiClient.put('/routing-policy', body: policy.toJson()) as Map<String, dynamic>;
    return RoutingPolicy.fromJson(json);
  }
}

final routingRepositoryProvider =
    Provider<RoutingRepository>((ref) => RoutingRepository(ref.watch(apiClientProvider)));
