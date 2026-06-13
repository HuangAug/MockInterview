import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/shared/models/interview_message.dart';
import 'package:mobile/shared/models/interview_report.dart';
import 'package:mobile/shared/models/interview_session.dart';
import 'package:mobile/shared/models/job_role.dart';
import 'package:mobile/shared/models/pagination.dart';

void main() {
  group('JobRole', () {
    test('fromJson parses all fields correctly', () {
      final json = {
        'id': 'a1000001-0000-4000-8000-000000000001',
        'code': 'frontend',
        'nameZh': '前端工程师',
        'nameEn': 'Frontend Engineer',
        'description': '负责前端开发',
        'sortOrder': 1,
      };

      final role = JobRole.fromJson(json);

      expect(role.id, 'a1000001-0000-4000-8000-000000000001');
      expect(role.code, 'frontend');
      expect(role.nameZh, '前端工程师');
      expect(role.nameEn, 'Frontend Engineer');
      expect(role.description, '负责前端开发');
      expect(role.sortOrder, 1);
    });

    test('fromJson handles null description', () {
      final json = {
        'id': 'id',
        'code': 'backend',
        'nameZh': '后端',
        'nameEn': 'Backend',
        'sortOrder': 2,
      };

      final role = JobRole.fromJson(json);
      expect(role.description, isNull);
    });
  });

  group('InterviewMessage', () {
    test('fromJson parses all fields correctly', () {
      final json = {
        'id': 'msg-001',
        'sessionId': 'session-001',
        'role': 'interviewer',
        'content': '请做一下自我介绍',
        'audioUrl': null,
        'sequence': 1,
        'createdAt': '2026-06-12T10:30:00Z',
      };

      final message = InterviewMessage.fromJson(json);

      expect(message.id, 'msg-001');
      expect(message.sessionId, 'session-001');
      expect(message.role, 'interviewer');
      expect(message.content, '请做一下自我介绍');
      expect(message.audioUrl, isNull);
      expect(message.sequence, 1);
      expect(message.createdAt, DateTime.utc(2026, 6, 12, 10, 30));
    });

    test('fromJson handles candidate messages', () {
      final json = {
        'id': 'msg-002',
        'sessionId': 'session-001',
        'role': 'candidate',
        'content': '我叫张三...',
        'sequence': 2,
        'createdAt': '2026-06-12T10:31:00Z',
      };

      final message = InterviewMessage.fromJson(json);
      expect(message.role, 'candidate');
      expect(message.audioUrl, isNull);
    });
  });

  group('InterviewSession', () {
    test('fromJson parses all fields correctly', () {
      final json = {
        'id': 'session-001',
        'jobRoleId': 'role-001',
        'jobRoleName': '前端工程师',
        'difficulty': 'mid',
        'mode': 'text',
        'status': 'in_progress',
        'questionCount': 3,
        'maxQuestions': 8,
        'reportStatus': 'pending',
        'startedAt': '2026-06-12T10:30:00Z',
        'endedAt': null,
        'createdAt': '2026-06-12T10:29:00Z',
        'updatedAt': '2026-06-12T10:32:00Z',
      };

      final session = InterviewSession.fromJson(json);

      expect(session.id, 'session-001');
      expect(session.jobRoleId, 'role-001');
      expect(session.jobRoleName, '前端工程师');
      expect(session.difficulty, 'mid');
      expect(session.mode, 'text');
      expect(session.status, 'in_progress');
      expect(session.questionCount, 3);
      expect(session.maxQuestions, 8);
      expect(session.reportStatus, 'pending');
      expect(session.startedAt, DateTime.utc(2026, 6, 12, 10, 30));
      expect(session.endedAt, isNull);
      expect(session.messages, isEmpty);
    });

    test('fromJson includes messages when present', () {
      final json = {
        'id': 'session-001',
        'jobRoleId': 'role-001',
        'jobRoleName': '前端工程师',
        'difficulty': 'mid',
        'mode': 'text',
        'status': 'in_progress',
        'questionCount': 1,
        'maxQuestions': 8,
        'reportStatus': 'pending',
        'startedAt': '2026-06-12T10:30:00Z',
        'endedAt': null,
        'createdAt': '2026-06-12T10:29:00Z',
        'updatedAt': '2026-06-12T10:30:00Z',
        'messages': [
          {
            'id': 'msg-001',
            'sessionId': 'session-001',
            'role': 'interviewer',
            'content': 'Q1',
            'sequence': 1,
            'createdAt': '2026-06-12T10:30:00Z',
          },
        ],
      };

      final session = InterviewSession.fromJson(json);
      expect(session.messages, hasLength(1));
      expect(session.messages.first.content, 'Q1');
    });
  });

  group('InterviewSessionListItem', () {
    test('fromJson parses list item fields', () {
      final json = {
        'id': 'session-001',
        'jobRoleName': '前端工程师',
        'difficulty': 'mid',
        'mode': 'text',
        'status': 'completed',
        'questionCount': 8,
        'reportStatus': 'ready',
        'overallScore': 85.50,
        'createdAt': '2026-06-12T10:29:00Z',
      };

      final item = InterviewSessionListItem.fromJson(json);

      expect(item.id, 'session-001');
      expect(item.jobRoleName, '前端工程师');
      expect(item.overallScore, 85.50);
      expect(item.status, 'completed');
      expect(item.reportStatus, 'ready');
    });
  });

  group('QuestionFeedbackItem', () {
    test('fromJson parses all fields', () {
      final json = {
        'sequence': 1,
        'question': '请自我介绍',
        'answerSummary': '候选人做了自我介绍',
        'score': 80.0,
        'feedback': '可以更结构化的表达',
      };

      final item = QuestionFeedbackItem.fromJson(json);

      expect(item.sequence, 1);
      expect(item.question, '请自我介绍');
      expect(item.answerSummary, '候选人做了自我介绍');
      expect(item.score, 80.0);
      expect(item.feedback, '可以更结构化的表达');
    });
  });

  group('InterviewReport', () {
    test('fromJson parses all fields correctly', () {
      final json = {
        'id': 'report-001',
        'sessionId': 'session-001',
        'overallScore': 82.50,
        'communicationScore': 85.00,
        'technicalScore': 78.00,
        'problemSolvingScore': 80.00,
        'structureScore': 87.00,
        'strengths': ['表达能力好', '逻辑清晰'],
        'weaknesses': ['技术深度不足'],
        'suggestions': ['多练习算法题', '学习系统设计'],
        'questionFeedback': [
          {
            'sequence': 1,
            'question': '请自我介绍',
            'answerSummary': '自我介绍',
            'score': 85.0,
            'feedback': '不错',
          },
        ],
        'summary': '总体表现良好，有提升空间。',
        'createdAt': '2026-06-12T10:35:00Z',
      };

      final report = InterviewReport.fromJson(json);

      expect(report.id, 'report-001');
      expect(report.sessionId, 'session-001');
      expect(report.overallScore, 82.50);
      expect(report.communicationScore, 85.00);
      expect(report.technicalScore, 78.00);
      expect(report.problemSolvingScore, 80.00);
      expect(report.structureScore, 87.00);
      expect(report.strengths, ['表达能力好', '逻辑清晰']);
      expect(report.weaknesses, ['技术深度不足']);
      expect(report.suggestions, ['多练习算法题', '学习系统设计']);
      expect(report.questionFeedback, hasLength(1));
      expect(report.summary, '总体表现良好，有提升空间。');
    });
  });

  group('ReportStatus', () {
    test('fromJson parses correctly', () {
      final json = {
        'sessionId': 'session-001',
        'reportStatus': 'generating',
      };

      final status = ReportStatus.fromJson(json);

      expect(status.sessionId, 'session-001');
      expect(status.reportStatus, 'generating');
    });
  });

  group('Pagination', () {
    test('fromJson parses all fields', () {
      final json = {
        'page': 1,
        'pageSize': 20,
        'total': 100,
        'totalPages': 5,
      };

      final pagination = Pagination.fromJson(json);

      expect(pagination.page, 1);
      expect(pagination.pageSize, 20);
      expect(pagination.total, 100);
      expect(pagination.totalPages, 5);
    });
  });
}