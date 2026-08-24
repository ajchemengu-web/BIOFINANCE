import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/transaction.dart';

class TransactionsRepository {
  TransactionsRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<List<AppTransaction>> list() async {
    final json = await _apiClient.get('/transactions') as List;
    return json.map((e) => AppTransaction.fromJson(e as Map<String, dynamic>)).toList();
  }
}

final transactionsRepositoryProvider =
    Provider<TransactionsRepository>((ref) => TransactionsRepository(ref.watch(apiClientProvider)));
