import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/provider_balance.dart';

class BalancesRepository {
  BalancesRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<BalancesResult> fetch() async {
    final json = await _apiClient.get('/balances') as Map<String, dynamic>;
    return BalancesResult.fromJson(json);
  }
}

final balancesRepositoryProvider =
    Provider<BalancesRepository>((ref) => BalancesRepository(ref.watch(apiClientProvider)));
