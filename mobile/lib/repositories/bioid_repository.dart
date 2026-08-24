import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/networking/api_client.dart';
import '../models/bio_id.dart';

class BioIdRepository {
  BioIdRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<BioId> fetchOrIssue() async {
    try {
      final json = await _apiClient.get('/bioid') as Map<String, dynamic>;
      return BioId.fromJson(json);
    } on Exception {
      final json = await _apiClient.post('/bioid') as Map<String, dynamic>;
      return BioId.fromJson(json);
    }
  }
}

final bioIdRepositoryProvider =
    Provider<BioIdRepository>((ref) => BioIdRepository(ref.watch(apiClientProvider)));
